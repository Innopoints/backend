"""Schema for the Project model."""

from marshmallow_enum import EnumField
from marshmallow import validate

from innopoints.extensions import ma, db
from innopoints.models import Project, ReviewStatus, LifetimeStage


# pylint: disable=missing-docstring

class ProjectSchema(ma.ModelSchema):
    class Meta:
        model = Project
        ordered = True
        sqla_session = db.session

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
