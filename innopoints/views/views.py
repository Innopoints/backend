"""Application views"""

from flask import abort, request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import (
    Competence,
)
from innopoints.schemas import (
    CompetenceSchema,
)

NO_PAYLOAD = ('', 204)
