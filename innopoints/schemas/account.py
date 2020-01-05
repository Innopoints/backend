"""Schema for the Account model."""

from innopoints.extensions import ma, db
from innopoints.models import Account


# pylint: disable=missing-docstring

class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        ordered = True
        sqla_session = db.session

    balance = ma.Int()


class TimelineSchema(ma.Schema):
    class Meta:
        ordered = True
        sqla_session = db.session

    entry_time = ma.DateTime(timezone=True)
    type = ma.Str()
    payload = ma.Dict()
