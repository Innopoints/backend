"""Model schemas for serialization."""

from marshmallow import validate, validates_schema, ValidationError, pre_load, post_dump
from innopoints.extensions import ma
from marshmallow_enum import EnumField

from .models import (
    Account,
    Activity,
    Application,
    ApplicationStatus,
    Color,
    Competence,
    LifetimeStage,
    Project,
    ReviewStatus,
    db
)


# pylint: disable=missing-docstring


class ListProjectSchema(ma.ModelSchema):
    class Meta:
        model = Project
        ordered = True
        sqla_session = db.session
        fields = (
            'id',
            'name',
            'image_url',
            'creation_time',
            'organizer',
            'moderators',
            'review_status',
            'activities',
        )

    class BriefActivitySchema(ma.ModelSchema):
        """Internal schema for a brief representation of activities within a project."""
        class Meta:
            model = Activity
            ordered = True
            sqla_session = db.session
            fields = (
                'id',
                'name',
                'dates',
                'vacant_spots',
                'competences',
            )

    review_status = EnumField(ReviewStatus)
    activities = ma.Nested(BriefActivitySchema, many=True)


class ProjectSchema(ma.ModelSchema):
    class Meta:
        model = Project
        ordered = True
        sqla_session = db.session
        exclude = ('notifications',)

    name = ma.Str(required=True,
                  validate=validate.Length(min=1, max=128),
                  error_messages={'required': 'A project name is required.',
                                  'validator_failed': 'The name must be between 1 and 128 chars.'})
    image_id = ma.Int()
    image_url = ma.Str(dump_only=True)
    review_status = EnumField(ReviewStatus)
    lifetime_stage = EnumField(LifetimeStage)
    activities = ma.Nested('ActivitySchema', many=True)
    moderators = ma.Nested('AccountSchema', only=('full_name', 'email'), many=True)


class ActivitySchema(ma.ModelSchema):
    class Meta:
        model = Activity
        ordered = True
        exclude = ('project_id', 'notifications')
        sqla_session = db.session

    @pre_load
    def unwrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
        """Expand the {"start": , "end": } dates object into two separate properties."""
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
        start = data['start_date']
        end = data['end_date']

        if start > end:
            raise ValidationError('The start date is beyond the end date.')

    def get_applications(self, activity):
        fields = ['id', 'applicant']
        filtering = {'activity_id': activity.id,
                     'status': ApplicationStatus.approved}

        if not self.context['user'].is_authenticated:
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
        if self.context['user'].is_authenticated:
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
                             deserialize='create_applications')
    existing_application = ma.Method(serialize='get_existing_application',
                                     dump_only=True)


class ApplicationSchema(ma.ModelSchema):
    class Meta:
        model = Application
        ordered = True
        sqla_session = db.session
        exclude = ('report', 'feedback')

    status = EnumField(ApplicationStatus)
    applicant = ma.Nested('AccountSchema', only=('full_name', 'email'))
    telegram_username = ma.Str(data_key='telegram')


class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account
        ordered = True
        sqla_session = db.session


class CompetenceSchema(ma.ModelSchema):
    class Meta:
        model = Competence
        ordered = True
        sqla_session = db.session
        exclude = ('activities', 'feedback')


class ColorSchema(ma.ModelSchema):
    class Meta:
        model = Color
        ordered = True
        sqla_session = db.session
        exclude = ('varieties',)

    @pre_load
    def normalize_value(self, data, **kwargs):  # pylint: disable=unused-argument
        """Normalize the color value, stripping the '#' and transforming symbols to uppercase."""
        if data['value'].startswith('#'):
            data['value'] = data['value'][1:]

        if len(data['value']) != 6:
            raise ValidationError(
                f'The color value is {len(data["value"])} characters long, 6 expected.')

        data['value'] = data['value'].upper()

        if not all(char in '0123456789ABCDEF' for char in data['value']):
            raise ValidationError('The color value contains non-hex symbols.')
        
        return data

    @post_dump
    def precede_hash(self, data, **kwargs):  # pylint: disable=unused-argument
        """Precede the value of the color with a '#' symbol."""
        data['value'] = '#' + data['value']
        return data
