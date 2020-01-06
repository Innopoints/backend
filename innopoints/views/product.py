"""Views related to the Product model.

Product:
- GET    /products
- POST   /products
- GET    /products/{product_id}
- PATCH  /products/{product_id}
- DELETE /products/{product_id}
"""

import logging
import math
from datetime import date

from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.notifications import notify_all
from innopoints.extensions import db
from innopoints.models import Product, Notification, Account, NotificationType
from innopoints.schemas import ProductSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/products')
def list_products():
    """List products available in InnoStore."""
    default_limit = 24
    default_page = 1
    default_order_by = 'addition_time'
    default_order = 'asc'
    ordering = {
        ('addition_time', 'asc'): Product.addition_time.asc(),
        ('addition_time', 'desc'): Product.addition_time.desc(),
        ('price', 'asc'): Product.price.asc(),
        ('price', 'desc'): Product.price.desc()
    }

    try:
        limit = int(request.args.get('limit', default_limit))
        page = int(request.args.get('page', default_page))
        order_by = request.args.get('order_by', default_order_by)
        order = request.args.get('order', default_order)
    except ValueError:
        abort(400, {'message': 'Bad query parameters.'})

    if limit < 1 or page < 1:
        abort(400, {'message': 'Limit and page number must be positive.'})

    if (order_by, order) not in ordering:
        abort(400, {'message': 'Invalid ordering specified.'})

    db_query = Product.query
    count_query = db.session.query(db.func.count(Product.id))
    if 'q' in request.args:
        like_query = f'%{request.args["q"]}%'
        or_condition = or_(Product.name.ilike(like_query),
                           Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition)
        count_query = count_query.filter(or_condition)
    db_query = db_query.order_by(ordering[order_by, order])
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    schema = ProductSchema(many=True, exclude=('description',
                                               'varieties.stock_changes',
                                               'varieties.product',
                                               'varieties.product_id'))
    return jsonify(pages=math.ceil(count_query.scalar() / limit),
                   data=schema.dump(db_query.all()))


@api.route('/products', methods=['POST'])
@login_required
def create_product():
    """Create a new product."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

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

    @login_required
    def patch(self, product_id):
        """Edit the product."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        if not current_user.is_admin:
            abort(401)
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

    @login_required
    def delete(self, product_id):
        """Delete the product."""
        if not current_user.is_admin:
            abort(401)
        product = Product.query.get_or_404(product_id)

        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


product_api = ProductDetailAPI.as_view('product_api')
api.add_url_rule('/products/<int:product_id>',
                 view_func=product_api,
                 methods=('GET', 'PATCH', 'DELETE'))
