from innopoints.extensions import ma, db
from innopoints.models import Account


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        ordered = True
        sqla_session = db.session
