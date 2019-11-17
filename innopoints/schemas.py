"""Model schemas for serialization."""

from marshmallow import validate, validates_schema, ValidationError, pre_load
from flask_marshmallow import Marshmallow
from marshmallow_enum import EnumField

from .models import (
    Activity,
    LifetimeStage,
    Project,
    ReviewStatus,
    db
)

ma = Marshmallow()


class ListProjectSchema(ma.ModelSchema):
    """Schema for listing projects."""
    class Meta:  # pylint: disable=missing-docstring
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
        class Meta:  # pylint: disable=missing-docstring
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
    """Schema for viewing and updating projects."""
    class Meta:  # pylint: disable=missing-docstring
        model = Project
        sqla_session = db.session

    name = ma.Str(required=True,
                  validate=validate.Length(min=1, max=128),
                  error_messages={'required': 'A project name is required.',
                                  'validator_failed': 'The name must be between 1 and 128 chars.'})
    image_id = ma.Int()
    review_status = EnumField(ReviewStatus)
    lifetime_stage = EnumField(LifetimeStage)
    activities = ma.Nested('ActivitySchema', many=True)


class ActivitySchema(ma.ModelSchema):
    """Schema for activities."""
    class Meta:  # pylint: disable=missing-docstring
        model = Activity
        ordered = True
        exclude = ('project_id',)
        sqla_session = db.session

    @pre_load
    def unwrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
        """Expand the {"start": , "end": } dates object into two separate properties."""
        try:
            dates = data.pop('dates')
            data['start_date'] = dates['start']
            data['end_date'] = dates['end']
        except KeyError:
            raise ValidationError("The date range has a wrong format.")

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


    work_hours = ma.Int(validate=validate.Range(min=1))
    reward_rate = ma.Int(validate=validate.Range(min=1))
    people_required = ma.Int(validate=validate.Range(min=0))
    application_deadline = ma.DateTime(format='iso', data_key='deadline')
