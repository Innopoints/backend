"""Schema for a notification."""

from marshmallow import pre_dump
from marshmallow_enum import EnumField

from innopoints.extensions import ma
from innopoints.models import (
    Notification, NotificationType,
    Project,
    Activity,
    Product,
    Variety,
    Account,
    Application,
    StockChange,
    Transaction,
)


# pylint: disable=missing-docstring

class PayloadSchema(ma.Schema):
    project = ma.Nested('ProjectSchema', only=('id', 'name', 'review_status', 'lifetime_stage'))
    activity = ma.Nested('ActivitySchema', only=('id', 'name'))
    product = ma.Nested('ProductSchema', only=('id', 'name', 'type', 'price'))
    variety = ma.Nested('VarietySchema', only=('id', 'size', 'color'))
    account = ma.Nested('AccountSchema', only=('email', 'full_name'))
    application = ma.Nested('ApplicationSchema', only=('id', 'status', 'actual_hours'))
    stock_change = ma.Nested('StockChangeSchema', only=('id', 'amount', 'status'))
    transaction = ma.Nested('TransactionSchema', only=('id', 'change'))

    @pre_dump
    def fill_data(self, data, **kwargs):  # pylint: disable=unused-argument
        if 'project_id' in data:
            data['project'] = Project.query.get(data.pop('project_id'))
        if 'activity_id' in data:
            data['activity'] = Activity.query.get(data.pop('activity_id'))
        if 'product_id' in data:
            data['product'] = Product.query.get(data.pop('product_id'))
        if 'variety_id' in data:
            data['variety'] = Variety.query.get(data.pop('variety_id'))
        if 'account_email' in data:
            data['account'] = Account.query.get(data.pop('account_email'))
        if 'application_id' in data:
            data['application'] = Application.query.get(data.pop('application_id'))
        if 'stock_change_id' in data:
            data['stock_change'] = StockChange.query.get(data.pop('stock_change_id'))
        if 'transaction_id' in data:
            data['transaction'] = Transaction.query.get(data.pop('transaction_id'))
        return data


class NotificationSchema(ma.ModelSchema):
    class Meta:
        model = Notification
    type = EnumField(NotificationType)
    payload = ma.Nested(PayloadSchema)