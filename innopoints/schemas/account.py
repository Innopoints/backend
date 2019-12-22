"""Schema for the Account model."""

from innopoints.extensions import ma, db
from innopoints.models import Account


# pylint: disable=missing-docstring

class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        ordered = True
        sqla_session = db.session
