"""Schema for the Application model."""

from marshmallow_enum import EnumField

from innopoints.extensions import ma, db
from innopoints.models import Application, ApplicationStatus


# pylint: disable=missing-docstring

class ApplicationSchema(ma.ModelSchema):
    class Meta:
        model = Application
        ordered = True
        sqla_session = db.session
        exclude = ('report', 'feedback')

    status = EnumField(ApplicationStatus)
    applicant = ma.Nested('AccountSchema', only=('full_name', 'email'))
    telegram_username = ma.Str(data_key='telegram')
