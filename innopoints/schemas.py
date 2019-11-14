"""Model schemas for serialization"""

from enum import Enum

from marshmallow import validate, validates, ValidationError
from flask_marshmallow import Marshmallow
from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import field_for

from .models import (
    Activity,
    LifetimeStage,
    Project,
    ReviewStatus,
)

ma = Marshmallow()


class ActivitySchema(ma.ModelSchema):
    """Schema for activities"""
    class Meta:  # pylint: disable=missing-docstring
        model = Activity


# {
# 		"id": int,
# 		"name": str,
# 		"img": str,  // URL
# 		"creation_time": str,  // ISO format
# 		"organizer": str,
#
# 		"review_status": str,  // only returned to admins
# 		"activities": [
# 			{
#               "id",
# 				"name": str,
# 				"dates": {
# 					// ISO format: yyyy-mm-dd
# 					"start": str,
# 					"end": str,
# 				},
# 				"vacant_spots",  // computed from "people_required"
#                          // and count of accepted applications
# 				"competences": [int],
# 			},
# 		],
# 	},

class ListProjectSchema(ma.ModelSchema):
    """Schema for listing projects"""
    class Meta:  # pylint: disable=missing-docstring
        model = Project
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
        """Internal schema for a brief representation of activities within a project"""
        class Meta:  # pylint: disable=missing-docstring
            model = Activity
            fields = (
                'id',
                'name',
                'dates',
                'vacant_spots',
                'competences',
            )

    review_status = EnumField(ReviewStatus)
    activities = ma.Nested(BriefActivitySchema, many=True)
