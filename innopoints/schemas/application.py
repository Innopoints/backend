"""Schema for the Application and VolunteeringReport models."""

from marshmallow import validate, pre_load, ValidationError, validates
from marshmallow_enum import EnumField

from innopoints.extensions import ma
from innopoints.models import Application, ApplicationStatus, VolunteeringReport, Feedback


# pylint: disable=missing-docstring

class ApplicationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Application
        load_instance = True
        ordered = True
        include_relationships = True

    status = EnumField(ApplicationStatus)
    applicant = ma.Nested('AccountSchema', only=('full_name', 'email'))
    feedback = ma.Nested('FeedbackSchema', exclude=('time',))
    reports = ma.Nested('VolunteeringReportSchema', many=True)
    telegram_username = ma.Str(data_key='telegram')


class ActivityProjectSchema(ma.SQLAlchemyAutoSchema):
    '''An intermediate schema for VolunteeringReportSchema to get the project name.'''
    class Meta:
        model = Application
        load_instance = True
        fields = ('project', 'name')
        include_relationships = True

    project = ma.Nested('ProjectSchema', only=('name', 'id'))


class ApplicationActivitySchema(ma.SQLAlchemyAutoSchema):
    '''An intermediate schema for VolunteeringReportSchema to get the activity name.'''
    class Meta:
        model = Application
        load_instance = True
        fields = ('activity',)
        include_relationships = True

    activity = ma.Nested('ActivityProjectSchema')


class VolunteeringReportSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = VolunteeringReport
        load_instance = True
        ordered = True
        include_fk = True
        include_relationships = True

    reporter_email = ma.Str(dump_only=True)
    application_id = ma.Int(dump_only=True)
    application = ma.Nested('ApplicationActivitySchema', data_key='application_on')
    rating = ma.Int(validate=validate.Range(min=1, max=5))


class FeedbackSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Feedback
        load_instance = True
        ordered = True
        include_relationships = True
        exclude = ('transaction',)

    @pre_load
    def wrap_competences(self, data, **_kwargs):
        """Turn a flat list of competence IDs into a list of objects."""
        data['competences'] = [{'id': comp_id} for comp_id in data['competences']]
        return data

    @validates('competences')
    def ensure_competence_amount(self, competences):
        if len(competences) not in range(1, 4):
            raise ValidationError('Must include 1-3 competences.')

    answers = ma.List(ma.Str(), required=True)
