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


class ActivityProjectSchema(ma.ModelSchema):
    '''An intermediate schema for VolunteeringReportSchema to get the project name.'''
    class Meta:
        model = Application
        fields = ('project', 'name')
        sqla_session = db.session

    project = ma.Nested('ProjectSchema', only=('name', 'id'))


class ApplicationActivitySchema(ma.ModelSchema):
    '''An intermediate schema for VolunteeringReportSchema to get the activity name.'''
    class Meta:
        model = Application
        fields = ('activity',)
        sqla_session = db.session

    activity = ma.Nested('ActivityProjectSchema')


class VolunteeringReportSchema(ma.ModelSchema):
    class Meta:
        model = VolunteeringReport
        ordered = True
        include_fk = True
        sqla_session = db.session

    reporter_email = ma.Str(dump_only=True)
    application_id = ma.Int(dump_only=True)
    application = ma.Nested('ApplicationActivitySchema', data_key='application_on')
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
