"""Views related to the Product model.

Product:
- GET    /products
- POST   /products
- GET    /products/{product_id}
- PATCH  /products/{product_id}
- DELETE /products/{product_id}
"""

import json
import logging
import math
from datetime import date

from flask import request, jsonify
from flask.views import MethodView
from flask_login import current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort, admin_required
from innopoints.core.notifications import notify_all, remove_notifications
from innopoints.extensions import db
from innopoints.models import (
    Account,
    Notification,
    NotificationType,
    Product,
    StockChange,
    StockChangeStatus,
    Variety,
)
from innopoints.schemas import ProductSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/products')
def list_products():
    """List products available in InnoStore."""
    # pylint: disable=invalid-unary-operand-type
    purchases = (
        db.session.query(StockChange.variety_id,
                         db.func.sum(StockChange.amount).label('variety_purchases'))
            .join(StockChange.account)
            .filter(StockChange.amount < 0,
                    StockChange.status != StockChangeStatus.rejected,
                    ~Account.is_admin)
            .group_by(StockChange.variety_id).subquery()
    )
    color_array = db.func.ARRAY_AGG(Variety.color)
    default_limit = 24
    default_page = 1
    default_order_by = 'addition_time'
    default_order = 'desc'
    ordering = {
        ('addition_time', 'asc'): Product.addition_time.asc(),
        ('addition_time', 'desc'): Product.addition_time.desc(),
        ('price', 'asc'): Product.price.asc(),
        ('price', 'desc'): Product.price.desc(),
        ('purchases', 'asc'): db.nullsfirst(db.asc(-db.func.sum(purchases.c.variety_purchases))),
        ('purchases', 'desc'): db.nullslast(db.desc(-db.func.sum(purchases.c.variety_purchases))),
    }

    try:
        limit = int(request.args.get('limit', default_limit))
        page = int(request.args.get('page', default_page))
        order_by = request.args.get('order_by', default_order_by)
        order = request.args.get('order', default_order)
        excluded_colors = request.args.getlist('excluded_colors', type=str)
        min_price = request.args.get('min_price', 0, int)
        max_price = request.args.get('max_price', type=int)
    except ValueError:
        abort(400, {'message': 'Bad query parameters.'})

    if max_price is not None and max_price < min_price:
        abort(400, {'message': 'Maximum price cannot be lower than minimum.'})

    if not isinstance(excluded_colors, list) or not \
        all(item is None or isinstance(item, str) for item in excluded_colors):
        abort(400, {'message': 'Excluded colors has to be an array of strings and possibly null.'})

    if limit < 1 or page < 1:
        abort(400, {'message': 'Limit and page number must be positive.'})

    if (order_by, order) not in ordering:
        abort(400, {'message': 'Invalid ordering specified.'})

    db_query = Product.query
    if 'q' in request.args:
        like_query = f'%{request.args["q"]}%'
        or_condition = or_(Product.name.ilike(like_query),
                           Product.type.ilike(like_query),
                           Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition).distinct()

    if excluded_colors:
        db_query = db_query.join(Product.varieties)
        if '\x00' in excluded_colors:
            db_query = db_query.filter(Variety.color.isnot(None))
            excluded_colors.remove('\x00')
        excluded_colors = [color.lstrip('#') for color in excluded_colors]
        db_query = (
            db_query.group_by(Product)
                .having(~(color_array.cast(db.ARRAY(db.Text)).op('<@')(excluded_colors)))
        )

    if min_price > 0:
        db_query = db_query.filter(Product.price >= min_price)
    if max_price is not None:
        db_query = db_query.filter(Product.price <= max_price)

    count = db.session.query(db_query.subquery()).count()
    if order_by == 'purchases':
        if excluded_colors:
            abort(400, {'message': 'Ordering by purchases is not allowed when filtering.'})
        db_query = (
            db_query.join(Product.varieties)
                .outerjoin(purchases,
                           Variety.id == purchases.c.variety_id)
                .group_by(Product)
        )

    db_query = db_query.order_by(ordering[order_by, order])
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    schema = ProductSchema(many=True, exclude=('description',
                                               'varieties.stock_changes',
                                               'varieties.product',
                                               'varieties.product_id'))
    return jsonify(pages=math.ceil(count / limit),
                   data=schema.dump(db_query.all()))


@api.route('/products', methods=['POST'])
@admin_required
def create_product():
    """Create a new product."""
    in_schema = ProductSchema(exclude=('id', 'addition_time',
                                       'varieties.stock_changes.variety_id',
                                       'varieties.product_id',
                                       'varieties.images.variety_id'),
                              context={'user': current_user})

    try:
        new_product = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    duplicate = Product.query.filter_by(name=new_product.name, type=new_product.type)
    if db.session.query(duplicate.exists()).scalar():
        abort(400, {'message': 'A product with this name and type exists.'})

    if not new_product.varieties:
        abort(400, {'message': 'Please provide at least one variety.'})

    try:
        for variety in new_product.varieties:
            variety.product = new_product
            for stock_change in variety.stock_changes:
                stock_change.variety_id = variety.id

        db.session.add(new_product)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    # TODO: replace the following with proper debounce
    # Check if a notification has been sent today
    already_sent = Notification.query.filter(
        Notification.type == NotificationType.new_arrivals,
        Notification.timestamp >= date.today()
    ).exists()
    if not db.session.query(already_sent).scalar():
        users = Account.query.filter_by(is_admin=False).all()
        notify_all(users, NotificationType.new_arrivals)

    out_schema = ProductSchema(exclude=('varieties.product_id',
                                        'varieties.product',
                                        'varieties.images.variety_id',
                                        'varieties.images.id',
                                        'varieties.stock_changes'))
    return out_schema.jsonify(new_product)


class ProductDetailAPI(MethodView):
    """REST views for the Product model"""
    def get(self, product_id):
        """Get a single product."""
        product = Product.query.get_or_404(product_id)
        schema = ProductSchema(exclude=('varieties.stock_changes',
                                        'varieties.product',
                                        'varieties.product_id'))
        return schema.jsonify(product)

    @admin_required
    def patch(self, product_id):
        """Edit the product."""
        product = Product.query.get_or_404(product_id)

        in_out_schema = ProductSchema(exclude=('id', 'varieties', 'addition_time'))

        try:
            updated_product = in_out_schema.load(request.json, instance=product, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_product)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

        return in_out_schema.jsonify(updated_product)

    @admin_required
    def delete(self, product_id):
        """Delete the product."""
        product = Product.query.get_or_404(product_id)

        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})
        remove_notifications({
            'product_id': product_id,
        })
        return NO_PAYLOAD


product_api = ProductDetailAPI.as_view('product_api')
api.add_url_rule('/products/<int:product_id>',
                 view_func=product_api,
                 methods=('GET', 'PATCH', 'DELETE'))
