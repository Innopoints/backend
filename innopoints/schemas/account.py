"""Schema for the Account model."""

from marshmallow import validate

from innopoints.extensions import ma
from innopoints.models import Account, Transaction


# pylint: disable=missing-docstring

class AccountSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Account
        ordered = True
        include_relationships = True

    def get_csrf_token(self, _account):
        return self.context.get('csrf_token')

    balance = ma.Int()
    csrf_token = ma.Method(serialize='get_csrf_token', dump_only=True)


class TransactionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Transaction
        ordered = True
        include_relationships = True


class TimelineSchema(ma.Schema):
    class Meta:
        ordered = True

    entry_time = ma.DateTime(timezone=True)
    type = ma.Str()
    payload = ma.Dict()


class NotificationSettingsSchema(ma.Schema):
    class Meta:
        ordered = True
        notification_modes = ['off', 'email', 'push']

    innostore = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    volunteering = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    project_creation = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    administration = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    service = ma.Str(validate=validate.OneOf(Meta.notification_modes))
