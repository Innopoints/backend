"""Schema for the Activity and Competence models."""

from marshmallow import validate, validates_schema, ValidationError, pre_load, post_dump

from innopoints.extensions import ma, db
from innopoints.models import Activity, Application, ApplicationStatus, Competence
from .application import ApplicationSchema


# pylint: disable=missing-docstring

class ActivitySchema(ma.ModelSchema):
    class Meta:
        model = Activity
        ordered = True
        exclude = ('project_id', 'notifications')
        sqla_session = db.session

    @pre_load
    def unwrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
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
    def wrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
        """Collapse the two date properties into the {"start": , "end": } dates object."""
        data['timeframe'] = {
            'start': data.pop('start_date'),
            'end': data.pop('end_date')
        }
        return data

    @validates_schema
    def work_hours_mutex(self, data, **kwargs):  # pylint: disable=unused-argument
        """Ensure that working hours aren't specified along with the reward_rate."""
        if 'work_hours' in data and 'reward_rate' in data:
            raise ValidationError('Working hours and reward rate are mutually exclusive.')

    @validates_schema
    def valid_date_range(self, data, **kwargs):  # pylint: disable=unused-argument
        """Ensure that the start date is not beyond the end date."""
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise ValidationError('The start date is beyond the end date.')

    def get_applications(self, activity):
        """Retrieve the applications for a particular activity."""
        fields = ['id', 'applicant']
        filtering = {'activity_id': activity.id,
                     'status': ApplicationStatus.approved}

        if 'user' not in self.context or not self.context['user'].is_authenticated:
            return None

        if self.context['user'] in activity.project.moderators:
            filtering.pop('status')
            fields.append('telegram_username')
            fields.append('comment')

        appl_schema = ApplicationSchema(only=fields, many=True)
        applications = Application.query.filter_by(**filtering)
        return appl_schema.dump(applications.all())

    def get_existing_application(self, activity):
        """Using the user information from the context, provide a shorthand
        for the existing application of a volunteer."""
        appl_schema = ApplicationSchema(only=('id', 'telegram_username', 'comment'))
        if 'user' in self.context and self.context['user'].is_authenticated:
            application = Application.query.filter_by(applicant_email=self.context['user'].email,
                                                      activity_id=activity.id).one_or_none()
            if application is None:
                return None
            return appl_schema.dump(application)
        return None

    working_hours = ma.Int(validate=validate.Range(min=1))
    reward_rate = ma.Int(validate=validate.Range(min=1))
    people_required = ma.Int(validate=validate.Range(min=0))
    application_deadline = ma.DateTime(format='iso', data_key='application_deadline')
    vacant_spots = ma.Int(dump_only=True)
    applications = ma.Method(serialize='get_applications',
                             dump_only=True)
    existing_application = ma.Method(serialize='get_existing_application',
                                     dump_only=True)


class CompetenceSchema(ma.ModelSchema):
    class Meta:
        model = Competence
        ordered = True
        sqla_session = db.session
        exclude = ('activities', 'feedback')
