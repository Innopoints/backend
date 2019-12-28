"""Views related to the Variety model.

Variety:
- POST   /products/{product_id}/variety
- PATCH  /products/{product_id}/variety/{variety_id}
- DELETE /products/{product_id}/variety/{variety_id}
- POST   /products/{product_id}/variety/{variety_id}/purchase

Size:
- GET /sizes
- POST /sizes

Color:
- GET /colors
- POST /colors
"""

import logging

from flask import abort, request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import (
    Account,
    Color,
    Product,
    Size,
    StockChange,
    StockChangeStatus,
    Transaction,
    Variety,
)
from innopoints.schemas import (
    ColorSchema,
    SizeSchema,
    StockChangeSchema,
    VarietySchema,
)
from innopoints.core.notifications import notify_all

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/products/<int:product_id>/variety', methods=['POST'])
@login_required
def create_variety(product_id):
    """Create a new variety."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    product = Product.query.get_or_404(product_id)

    in_schema = VarietySchema(exclude=('id', 'product_id', 'product',
                                       'images.variety_id', 'stock_changes.variety_id',),
                              context={'user': current_user})

    try:
        new_variety = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        new_variety.product = product

        db.session.add(new_variety)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = VarietySchema(exclude=('product_id',
                                        'product',
                                        'images.variety_id',
                                        'images.id'))
    return out_schema.jsonify(new_variety)


class VarietyAPI(MethodView):
    """REST views for a particular instance of the Variety model."""

    @login_required
    def patch(self, product_id, variety_id):
        """Update the given variety."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        if not current_user.is_admin:
            abort(401)

        product = Product.query.get_or_404(product_id)
        variety = Variety.query.get_or_404(variety_id)
        if variety.product != product:
            abort(400, {'message': 'The specified product and variety are unrelated.'})

        in_schema = VarietySchema(exclude=('id', 'product_id', 'stock_changes.variety_id'),
                                  context={'update': True})

        amount = request.json.pop('amount', None)

        try:
            updated_variety = in_schema.load(request.json, instance=variety, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        if amount is not None:
            diff = amount - variety.amount
            if diff != 0:
                stock_change = StockChange(amount=diff,
                                           status=StockChangeStatus.carried_out,
                                           account=current_user,
                                           variety_id=updated_variety.id)
                db.session.add(stock_change)

        try:
            db.session.add(updated_variety)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = VarietySchema(exclude=('product_id', 'stock_changes', 'product', 'purchases'))
        return out_schema.jsonify(updated_variety)

    @login_required
    def delete(self, product_id, variety_id):
        """Delete the variety."""
        if not current_user.is_admin:
            abort(401)

        product = Product.query.get_or_404(product_id)
        variety = Variety.query.get_or_404(variety_id)
        if variety.product != product:
            abort(400, {'message': 'The specified product and variety are unrelated.'})

        try:
            db.session.delete(variety)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


variety_api = VarietyAPI.as_view('variety_api')
api.add_url_rule('/products/<int:product_id>/variety/<int:variety_id>',
                 view_func=variety_api,
                 methods=('PATCH', 'DELETE'))


@api.route('/products/<int:product_id>/variety/<int:variety_id>/purchase', methods=['POST'])
@login_required
def purchase_variety(product_id, variety_id):
    """Purchase a particular variety of a product."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    purchased_amount = request.json.get('amount')
    if not isinstance(purchased_amount, int):
        abort(400, {'message': 'The purchase amount must be specified as an integer.'})

    if purchased_amount <= 0:
        abort(400, {'message': 'The purchase amount must be positive.'})

    product = Product.query.get_or_404(product_id)
    variety = Variety.query.get_or_404(variety_id)

    if variety.product != product:
        abort(400, {'message': 'The specified product and variety are unrelated.'})

    log.debug(f'User with balance {current_user.balance} is trying to buy {purchased_amount} of a '
              f'product with a price of {product.price}. '
              f'Total = {product.price * purchased_amount}')
    if current_user.balance < product.price * purchased_amount:
        log.debug('Purchase refused: not enough points')
        abort(400, {'message': 'Insufficient funds.'})

    if purchased_amount > variety.amount:
        log.debug('Purchase refused: not enough stock')
        abort(400, {'message': 'Insufficient stock'})

    new_stock_change = StockChange(amount=-purchased_amount,
                                   status=StockChangeStatus.pending,
                                   account=current_user,
                                   variety_id=variety_id)
    db.session.add(new_stock_change)
    new_transaction = Transaction(account=current_user,
                                  change=-product.price * purchased_amount,
                                  stock_change_id=new_stock_change)
    new_stock_change.transaction = new_transaction
    db.session.add(new_transaction)

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})
    log.debug('Purchase successful')

    admins = Account.query.filter_by(is_admin=True).all()
    admin_emails = [admin.email for admin in admins]
    notify_all(admin_emails, 'new_purchase', {
        'account_email': current_user.email,
        'product_id': product.id,
        'variety_id': variety.id,
        'stock_change_id': new_stock_change.id,
    })

    out_schema = StockChangeSchema(exclude=('transaction', 'account', 'account_email'))
    return out_schema.jsonify(new_stock_change)


# ----- Size -----

@api.route('/sizes')
def list_sizes():
    """List all existing sizes."""
    schema = SizeSchema(many=True)
    return schema.jsonify(Size.query.all())


@api.route('/sizes', methods=['POST'])
@login_required
def create_size():
    """Create a new size."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_out_schema = SizeSchema()

    try:
        new_size = in_out_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_size)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return in_out_schema.jsonify(new_size)


# ----- Color -----

@api.route('/colors')
def list_colors():
    """List all existing colors."""
    schema = ColorSchema(many=True)
    return schema.jsonify(Color.query.all())


@api.route('/colors', methods=['POST'])
@login_required
def create_color():
    """Create a new color."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_out_schema = ColorSchema()

    try:
        new_color = in_out_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_color)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return in_out_schema.jsonify(new_color)
