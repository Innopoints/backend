"""Schema for a notification."""

from marshmallow import pre_dump, post_dump
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
)
from innopoints.schemas import (
    ProjectSchema,
    ActivitySchema,
    ProductSchema,
    VarietySchema,
    AccountSchema,
    ApplicationSchema,
)

# pylint: disable=missing-docstring

class PayloadSchema(ma.Schema):
    project = ma.Nested('ProjectSchema', only=('id', 'name'))
    activity = ma.Nested('ActivitySchema', only=('id', 'name'))
    product = ma.Nested('ProductSchema', only=('id', 'name', 'type'))
    variety = ma.Nested('VarietySchema', only=('id', 'size', 'color'))
    account = ma.Nested('AccountSchema', only=('email', 'full_name'))
    application = ma.Nested('ApplicationSchema', only=('applicant_email', 'status'))

    @pre_dump
    def fill_data(self, data, **kwargs):
        print(data)
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
        return data


class NotificationSchema(ma.ModelSchema):
    class Meta:
        model = Notification
    type = EnumField(NotificationType)
    payload = ma.Nested(PayloadSchema)
