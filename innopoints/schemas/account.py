"""Schema for the Account model."""

from marshmallow import validate

from innopoints.extensions import ma, db
from innopoints.models import Account, Transaction


# pylint: disable=missing-docstring

class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        ordered = True
        sqla_session = db.session

    balance = ma.Int()


class TransactionSchema(ma.ModelSchema):
    class Meta:
        model = Transaction
        ordered = True
        sqla_session = db.session


class TimelineSchema(ma.Schema):
    class Meta:
        ordered = True
        sqla_session = db.session

    entry_time = ma.DateTime(timezone=True)
    type = ma.Str()
    payload = ma.Dict()


class NotificationSettingsSchema(ma.Schema):
    class Meta:
        ordered = True
        sqla_session = db.session
        notification_modes = ['off', 'email', 'push']

    innostore = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    volunteering = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    project_creation = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    administration = ma.Str(validate=validate.OneOf(Meta.notification_modes))
    service = ma.Str(validate=validate.OneOf(Meta.notification_modes))
