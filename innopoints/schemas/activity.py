"""Schema for the Activity and Competence models."""

from marshmallow import validate, validates_schema, ValidationError, pre_load, post_dump

from innopoints.extensions import ma
from innopoints.models import Activity, Application, ApplicationStatus, Competence
from .application import ApplicationSchema


# pylint: disable=missing-docstring

class CompetenceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Competence
        load_instance = True
        ordered = True


class ActivitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Activity
        load_instance = True
        ordered = True
        include_relationships = True

    @pre_load
    def unwrap_dates(self, data, **_kwargs):
        """Expand the {"start": , "end": } dates object into two separate properties."""
        if 'timeframe' not in data:
            return data

        try:
            dates = data.pop('timeframe')
            data['start_date'] = dates['start']
            data['end_date'] = dates['end']
        except KeyError:
            raise ValidationError("The date range has a wrong format.")

        return data

    @post_dump
    def wrap_dates(self, data, **_kwargs):
        """Collapse the two date properties into the {"start": , "end": } dates object."""
        if 'start_date' not in data:
            return data

        data['timeframe'] = {
            'start': data.pop('start_date'),
            'end': data.pop('end_date')
        }
        return data

    @validates_schema
    def work_hours_mutex(self, data, **_kwargs):
        """Ensure that working hours aren't specified along with the reward_rate."""
        if 'work_hours' in data and 'reward_rate' in data:
            raise ValidationError('Working hours and reward rate are mutually exclusive.')

    @validates_schema
    def valid_date_range(self, data, **_kwargs):
        """Ensure that the start date is not beyond the end date."""
        if data.get('start_date') is not None and data.get('end_date') is not None:
            if data['start_date'] > data['end_date']:
                raise ValidationError('The start date is beyond the end date.')

    def get_applications(self, activity):
        """Retrieve the applications for a particular activity.
           For non-moderators will only return the approved applications."""
        fields = ['id', 'applicant', 'status', 'application_time']
        filtering = {'activity_id': activity.id,
                     'status': ApplicationStatus.approved}

        if 'user' not in self.context or not self.context['user'].is_authenticated:
            return None

        if self.context['user'] in activity.project.moderators or self.context['user'].is_admin:
            filtering.pop('status')
            fields.append('telegram_username')
            fields.append('comment')
            fields.append('actual_hours')
            fields.append('feedback')
            fields.append('reports')

        appl_schema = ApplicationSchema(only=fields, many=True)
        applications = Application.query.filter_by(**filtering)
        return appl_schema.dump(applications.all())

    def get_existing_application(self, activity):
        """Using the user information from the context, provide a shorthand
        for the existing application of a volunteer."""
        appl_schema = ApplicationSchema(only=('id', 'telegram_username', 'comment',
                                              'actual_hours', 'status', 'feedback'))
        if 'user' in self.context and self.context['user'].is_authenticated:
            application = Application.query.filter_by(applicant_email=self.context['user'].email,
                                                      activity_id=activity.id).one_or_none()
            if application is None:
                return None
            return appl_schema.dump(application)
        return None

    working_hours = ma.Int(allow_none=True, validate=validate.Range(min=1))
    reward_rate = ma.Int(allow_none=True, validate=validate.Range(min=1))
    people_required = ma.Int(allow_none=True, validate=validate.Range(min=0))
    start_date = ma.AwareDateTime(allow_none=True, format='iso')
    end_date = ma.AwareDateTime(allow_none=True, format='iso')
    application_deadline = ma.AwareDateTime(allow_none=True, format='iso')
    competences = ma.Pluck(CompetenceSchema, 'id', many=True, validate=validate.Length(0, 3))
    vacant_spots = ma.Int(dump_only=True)
    applications = ma.Method(serialize='get_applications',
                             dump_only=True)
    existing_application = ma.Method(serialize='get_existing_application',
                                     dump_only=True)
