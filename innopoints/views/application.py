"""Views related to the Application and VolunteeringReport models.

Application:
- POST   /projects/{project_id}/activities/{activity_id}/applications
- DELETE /projects/{project_id}/activities/{activity_id}/applications

VolunteeringReport:
- GET  /projects/{project_id}/activities/{activity_id}/applications/{application_id}/report_info
- POST /projects/{project_id}/activities/{activity_id}/applications/{application_id}/report
"""

import logging

from flask import request
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.extensions import db
from innopoints.models import (
    Activity,
    Application,
    ApplicationStatus,
    LifetimeStage,
    Project,
    project_moderation,
    VolunteeringReport,
)
from innopoints.schemas import ApplicationSchema, VolunteeringReportSchema


NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)

@api.route('/projects/<int:project_id>/activities/<int:activity_id>/applications', methods=['POST'])
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


@api.route('/projects/<int:project_id>/activities/<int:activity_id>/applications',
           methods=['DELETE'])
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


# ----- VolunteeringReport -----

@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/report_info')
@login_required
def get_report_info(project_id, activity_id, application_id):
    """Get the reports from the moderators of the project and an average rating."""
    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if current_user not in project.moderators and not current_user.is_admin:
        abort(401)

    avg_rating = db.session.query(
        db.func.round(db.func.avg(VolunteeringReport.rating))
    ).join(Application).join(Activity).join(
        project_moderation,
        VolunteeringReport.reporter_email == project_moderation.c.account_email
    ).filter(
        Application.applicant_email == application.applicant_email,
        project_moderation.c.project_id == project_id,
    ).scalar() or 0

    reports = VolunteeringReport.query.join(Application).join(Activity).join(
        project_moderation,
        VolunteeringReport.reporter_email == project_moderation.c.account_email
    ).filter(
        Application.applicant_email == application.applicant_email,
        project_moderation.c.project_id == project_id,
    ).all()

    out_schema = VolunteeringReportSchema(only=('content', 'rating', 'time'), many=True)
    return jsonify(average_rating=int(avg_rating), reports=out_schema.dump(reports))


@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/report', methods=['POST'])
@login_required
def create_report(project_id, activity_id, application_id):
    """Create a volunteering report on an application."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if current_user not in project.moderators and not current_user.is_admin:
        abort(401)

    if not (project.lifetime_stage == LifetimeStage.ongoing
            and project.review_status is not None):
        abort(400, {'message': 'The project must be in the finalizing stage.'})

    in_schema = VolunteeringReportSchema(exclude=('time',))
    try:
        new_report = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    new_report.application_id = application_id
    new_report.reporter_email = current_user.email

    try:
        db.session.add(new_report)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = VolunteeringReportSchema()
    return out_schema.jsonify(new_report)
