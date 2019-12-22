"""Schema for the Project model."""

from marshmallow_enum import EnumField
from marshmallow import validate

from innopoints.extensions import ma, db
from innopoints.models import Project, Activity, ReviewStatus, LifetimeStage


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

    # pylint: disable=no-member
    review_status = EnumField(ReviewStatus)
    activities = ma.Nested(BriefActivitySchema, many=True)


class ProjectSchema(ma.ModelSchema):
    class Meta:
        model = Project
        ordered = True
        sqla_session = db.session
        exclude = ('notifications',)

    # pylint: disable=no-member
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
