"""Schema for the Application and VolunteeringReport models."""

from marshmallow import validate
from marshmallow_enum import EnumField

from innopoints.extensions import ma, db
from innopoints.models import Application, ApplicationStatus, VolunteeringReport


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


class VolunteeringReportSchema(ma.ModelSchema):
    class Meta:
        model = VolunteeringReport
        ordered = True
        sqla_session = db.session

    rating = ma.Int(validate=validate.Range(min=1, max=5))
