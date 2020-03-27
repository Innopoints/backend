"""Schema for the Application and VolunteeringReport models."""

from marshmallow import validate, pre_load, ValidationError, validates
from marshmallow_enum import EnumField

from innopoints.extensions import ma, db
from innopoints.models import Application, ApplicationStatus, VolunteeringReport, Feedback


# pylint: disable=missing-docstring

class ApplicationSchema(ma.ModelSchema):
    class Meta:
        model = Application
        ordered = True
        sqla_session = db.session

    status = EnumField(ApplicationStatus)
    applicant = ma.Nested('AccountSchema', only=('full_name', 'email'))
    feedback = ma.Nested('FeedbackSchema', exclude=('time',))
    telegram_username = ma.Str(data_key='telegram')


class VolunteeringReportSchema(ma.ModelSchema):
    class Meta:
        model = VolunteeringReport
        ordered = True
        sqla_session = db.session

    rating = ma.Int(validate=validate.Range(min=1, max=5))


class FeedbackSchema(ma.ModelSchema):
    class Meta:
        model = Feedback
        ordered = True
        sqla_session = db.session
        exclude = ('transaction',)

    @pre_load
    def wrap_competences(self, data, **kwargs):  # pylint: disable=unused-argument
        """Turn a flat list of competence IDs into a list of objects."""
        data['competences'] = [{'id': comp_id} for comp_id in data['competences']]
        return data

    @validates('competences')
    def ensure_competence_amount(self, competences):
        if len(competences) not in range(1, 4):
            raise ValidationError('Must include 1-3 competences.')

    answers = ma.List(ma.Str(), required=True)
