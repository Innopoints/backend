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
    project_id = ma.Int(load_only=True)
    activity_id = ma.Int(load_only=True)
    product_id = ma.Int(load_only=True)
    variety_id = ma.Int(load_only=True)
    account_email = ma.Str(load_only=True)
    application_id = ma.Int(load_only=True)

    project = ma.Nested('ProjectSchema', only=('id', 'name'), dump_only=True)
    activity = ma.Nested('ActivitySchema', only=('id', 'name'), dump_only=True)
    product = ma.Nested('ProductSchema', only=('id', 'name', 'type'), dump_only=True)
    variety = ma.Nested('VarietySchema', only=('id', 'size', 'color'), dump_only=True)
    account = ma.Nested('AccountSchema', only=('email', 'full_name'), dump_only=True)
    application = ma.Nested('ApplicationSchema', only=('applicant_email', 'status'), dump_only=True)

    @pre_dump
    def fill_data(self, data, **kwargs):
        print(data)
        # if 'project_id' in data:
        #     project = Project.query.get(data.pop('project_id'))
        #     data['project'] = ProjectSchema().dump(project)
        # if 'activity_id' in data:
        #     activity = Activity.query.get(data.pop('activity_id'))
        #     data['activity'] = ActivitySchema().dump(activity)
        if 'product_id' in data:
            product = Product.query.get(data.pop('product_id'))
            data['product'] = ProductSchema().dump(product)
        # if 'variety_id' in data:
        #     variety = Variety.query.get(data.pop('variety_id'))
        #     data['variety'] = VarietySchema().dump(variety)
        if 'account_email' in data:
            account = Account.query.get(data.pop('account_email'))
            data['account'] = AccountSchema().dump(account)
        # if 'application_id' in data:
        #     application = Application.query.get(data.pop('application_id'))
        #     data['application'] = ApplicationSchema().dump(application)
        return data


class NotificationSchema(ma.ModelSchema):
    class Meta:
        model = Notification
    type = EnumField(NotificationType)
    payload = ma.Nested(PayloadSchema)
