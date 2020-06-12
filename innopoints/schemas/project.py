"""Schema for the Project and Tag models."""

from marshmallow_enum import EnumField
from marshmallow import validate

from innopoints.extensions import ma
from innopoints.models import Project, ReviewStatus, LifetimeStage, Tag


# pylint: disable=missing-docstring

class ProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        load_instance = True
        ordered = True
        include_relationships = True

    name = ma.Str(allow_none=True,
                  validate=validate.Length(max=128),
                  error_messages={'validator_failed': 'The name must be below 128 characters.'})
    creator = ma.Nested('AccountSchema', only=('full_name', 'email'))
    image_id = ma.Int(allow_none=True)
    review_status = EnumField(ReviewStatus)
    lifetime_stage = EnumField(LifetimeStage)
    activities = ma.Nested('ActivitySchema', many=True)
    moderators = ma.Nested('AccountSchema', only=('full_name', 'email'), many=True)
    start_date = ma.DateTime()
    end_date = ma.DateTime()


class TagSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tag
        load_instance = True
        ordered = True
