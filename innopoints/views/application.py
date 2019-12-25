"""Views related to the Application model.

- POST /projects/{project_id}/activity/{activity_id}/apply
"""

import logging

from flask import abort, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import Application, Project, Activity, ApplicationStatus
from innopoints.schemas import ApplicationSchema


NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)

@api.route('/projects/<int:project_id>/activity/<int:activity_id>/apply', methods=['POST'])
@login_required
def apply_for_activity(project_id, activity_id):
    """Apply for volunteering on a particular activity."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    project = Project.query.get_or_404(project_id)
    activity = Activity.query.get_or_404(activity_id)
    if activity.project != project:
        abort(400, {'message': 'The specified project and activity are unrelated.'})

    if activity.has_application_from(current_user):
        abort(400, {'message': 'An application already exists.'})

    if activity.telegram_required and not isinstance(request.json.get('telegram'), str):
        abort(400, {'message': 'This activity requires a Telegram username.'})

    new_application = Application(applicant=current_user,
                                  activity_id=activity_id,
                                  comment=request.json.get('comment'),
                                  telegram_username=request.json.get('telegram'),
                                  status=ApplicationStatus.pending)
    db.session.add(new_application)
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = ApplicationSchema(exclude=('applicant', 'actual_hours'))
    return out_schema.jsonify(new_application)


@api.route('/projects/<int:project_id>/activity/<int:activity_id>/apply', methods=['DELETE'])
@login_required
def take_back_application(project_id, activity_id):
    """Take back a volunteering application on a particular activity."""
    project = Project.query.get_or_404(project_id)
    activity = Activity.query.get_or_404(activity_id)
    if activity.project != project:
        abort(400, {'message': 'The specified project and activity are unrelated.'})

    application = Application.query.filter_by(activity_id=activity_id,
                                              applicant=current_user).one_or_none()
    if application is None:
        abort(400, {'message': 'No application exists for this activity.'})

    db.session.delete(application)
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD
