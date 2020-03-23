"""Views related to the Variety, StockChange, Size and Color models.

Variety:
- POST   /products/{product_id}/varieties
- PATCH  /products/{product_id}/varieties/{variety_id}
- DELETE /products/{product_id}/varieties/{variety_id}
- POST   /products/{product_id}/varieties/{variety_id}/purchase

StockChange:
- GET   /stock_changes/for_review
- PATCH /stock_changes/{stock_change_id}/status

Size:
- GET /sizes
- POST /sizes

Color:
- GET /colors
- POST /colors
"""

import logging

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.notifications import notify_all, notify, remove_notifications
from innopoints.models import (
    Account,
    Color,
    NotificationType,
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

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/products/<int:product_id>/varieties', methods=['POST'])
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
        remove_notifications({
            'variety_id': variety_id,
        })
        return NO_PAYLOAD


variety_api = VarietyAPI.as_view('variety_api')
api.add_url_rule('/products/<int:product_id>/varieties/<int:variety_id>',
                 view_func=variety_api,
                 methods=('PATCH', 'DELETE'))


@api.route('/products/<int:product_id>/varieties/<int:variety_id>/purchase', methods=['POST'])
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
        abort(400, {'message': 'Insufficient stock.'})

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
    notify_all(admins, NotificationType.new_purchase, {
        'account_email': current_user.email,
        'product_id': product.id,
        'variety_id': variety.id,
        'stock_change_id': new_stock_change.id,
    })
    if variety.amount <= 0:
        notify_all(admins, NotificationType.out_of_stock, {
            'product_id': product.id,
            'variety_id': variety.id,
        })

    out_schema = StockChangeSchema(exclude=('transaction', 'account', 'account_email'))
    return out_schema.jsonify(new_stock_change)


# ----- StockChange -----

@api.route('/stock_changes/for_review')
@login_required
def get_purchases_for_review():
    """Get a list of purchases that require admin's attention."""
    if not current_user.is_admin:
        abort(401)

    db_query = StockChange.query.filter(
        StockChange.status.in_((StockChangeStatus.pending, StockChangeStatus.ready_for_pickup))
    )
    schema = StockChangeSchema(many=True, exclude=('transaction',))
    return schema.jsonify(db_query.all())


@api.route('/stock_changes/<int:stock_change_id>/status', methods=['PATCH'])
@login_required
def edit_purchase_status(stock_change_id):
    """Edit the status of a particular purchase."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    try:
        status = getattr(StockChangeStatus, request.json['status'])
    except (KeyError, AttributeError):
        abort(400, {'message': 'A valid stock change status must be specified.'})

    stock_change = StockChange.query.get_or_404(stock_change_id)
    if stock_change.status != status:
        variety = Variety.query.get(stock_change.variety_id)
        product = variety.product
        if status == StockChangeStatus.rejected:
            db.session.delete(stock_change.transaction)
            remove_notifications({
                'transaction_id': stock_change.transaction.id,
            })
        elif stock_change.status == StockChangeStatus.rejected:
            new_transaction = Transaction(account=stock_change.account,
                                          change=product.price * stock_change.amount,
                                          stock_change_id=stock_change.id)
            stock_change.transaction = new_transaction
            db.session.add(new_transaction)
        stock_change.status = status

        notify(stock_change.account_email, NotificationType.purchase_status_changed, {
            'stock_change_id': stock_change.id,
            'product_id': product.id,
            'variety_id': variety.id,
        })

        try:
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD


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
