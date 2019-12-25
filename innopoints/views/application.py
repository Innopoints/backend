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

    if activity.telegram_required and not isinstance(request.json.get('telegram_username'), str):
        abort(400, {'message': 'This activity requires a Telegram username.'})

    new_application = Application(applicant=current_user,
                                  activity_id=activity_id,
                                  comment=request.json.get('comment'),
                                  telegram_username=request.json.get('telegram_username'),
                                  status=ApplicationStatus.pending)
    db.session.add(new_application)
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})
