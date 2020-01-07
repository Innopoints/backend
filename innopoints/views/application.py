"""Views related to the Application, VolunteeringReport and Feedback models.

Application:
- POST   /projects/{project_id}/activities/{activity_id}/applications
- DELETE /projects/{project_id}/activities/{activity_id}/applications
- PATCH  /projects/{project_id}/activities/{activity_id}/applications/{application_id}/status

VolunteeringReport:
- GET  /projects/{project_id}/activities/{activity_id}/applications/{application_id}/report_info
- POST /projects/{project_id}/activities/{activity_id}/applications/{application_id}/report
"""

import logging

from flask import request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.notifications import notify, notify_all
from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db
from innopoints.models import (
    Activity,
    Application,
    ApplicationStatus,
    LifetimeStage,
    NotificationType,
    Project,
    project_moderation,
    Transaction,
    VolunteeringReport,
)
from innopoints.schemas import ApplicationSchema, VolunteeringReportSchema, FeedbackSchema


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
    if activity.internal:
        abort(404)

    if activity.project != project:
        abort(400, {'message': 'The specified project and activity are unrelated.'})

    if project.lifetime_stage != LifetimeStage.ongoing:
        abort(400, {'message': 'Applications may only be placed on ongoing projects.'})

    if activity.has_application_from(current_user):
        abort(400, {'message': 'An application already exists.'})

    if activity.telegram_required and not isinstance(request.json.get('telegram'), str):
        abort(400, {'message': 'This activity requires a Telegram username.'})

    if activity.application_deadline is not None and activity.application_deadline < tz_aware_now():
        abort(400, {'message': 'The application is past the deadline.'})

    new_application = Application(applicant=current_user,
                                  activity_id=activity_id,
                                  comment=request.json.get('comment'),
                                  telegram_username=request.json.get('telegram'),
                                  actual_hours=activity.working_hours,
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
    if activity.internal:
        abort(404)

    if activity.project != project:
        abort(400, {'message': 'The specified project and activity are unrelated.'})

    application = Application.query.filter_by(activity_id=activity_id,
                                              applicant=current_user).one_or_none()
    if application is None:
        abort(400, {'message': 'No application exists for this activity.'})

    if project.lifetime_stage != LifetimeStage.ongoing:
        abort(400, {'message': 'Applications may only be taken back from ongoing projects.'})

    db.session.delete(application)
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD


@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/status', methods=['PATCH'])
@login_required
def edit_application(project_id, activity_id, application_id):
    """Change the status or the actual hours of an application."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if current_user not in project.moderators and not current_user.is_admin:
        abort(401)

    if activity.internal:
        if project.lifetime_stage != LifetimeStage.finalizing:
            abort(400, {'message': 'Internal activity applications may only be edited '
                                   'in the finalizing stage.'})
    else:
        if project.lifetime_stage != LifetimeStage.ongoing:
            abort(400, {'message': 'The application may only be edited for ongoing projects.'})

    old_status = application.status
    if 'status' in request.json:
        if activity.internal:
            abort(400, {'message': 'Cannot modify the status of internal activities.'})
        try:
            status = getattr(ApplicationStatus, request.json['status'])
        except AttributeError:
            abort(400, {'message': 'A valid application status must be specified.'})
        application.status = status

    if 'actual_hours' in request.json:
        actual_hours = request.json['actual_hours']
        if not isinstance(actual_hours, int) or actual_hours < 0:
            abort(400, {'message': 'Actual hours must be a non-negative integer.'})

        if activity.fixed_reward:
            abort(400, {'Working hours may only be changed on hourly-rate activity applications.'})
        application.actual_hours = actual_hours

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    if application.status != old_status:
        notify(application.applicant_email, NotificationType.application_status_changed, {
            'activity_id': activity_id,
            'application_id': application_id,
        })

    out_schema = ApplicationSchema()
    return out_schema.jsonify(application)


# ----- VolunteeringReport -----

@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/report_info')
@login_required
def get_report_info(project_id, activity_id, application_id):
    """Get the reports from the moderators of the project and an average rating."""
    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    if activity.internal:
        abort(404)
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
    if activity.internal:
        abort(404)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if current_user not in project.moderators and not current_user.is_admin:
        abort(401)

    if project.lifetime_stage != LifetimeStage.finalizing:
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


# ----- Feedback -----

@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/feedback')
@login_required
def read_feedback(project_id, activity_id, application_id):
    """Get the feedback from a volunteer on a particular volunteering experience."""
    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if current_user not in project.moderators and not current_user.is_admin:
        abort(401)

    out_schema = FeedbackSchema()
    return out_schema.jsonify(application.feedback)


@api.route('/projects/<int:project_id>/activities/<int:activity_id>'
           '/applications/<int:application_id>/feedback', methods=['POST'])
@login_required
def leave_feedback(project_id, activity_id, application_id):
    """Leave feedback on a particular volunteering experience."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    application = Application.query.get_or_404(application_id)
    activity = Activity.query.get_or_404(activity_id)
    project = Project.query.get_or_404(project_id)

    if activity.project != project or application.activity_id != activity.id:
        abort(400, {'message': 'The specified project, activity and application are unrelated.'})

    if application.applicant != current_user:
        abort(401)

    if application.feedback is not None:
        abort(400, {'message': 'Feedback already exists.'})

    in_schema = FeedbackSchema(exclude=('time',))
    try:
        new_feedback = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    if len(new_feedback.answers) != len(activity.feedback_questions):
        abort(400, {'message': f'Expected {len(activity.feedback_questions)} answer(s), '
                               f'found {len(new_feedback.answers)}.'})
    new_feedback.application_id = application_id
    db.session.add(new_feedback)

    new_transaction = Transaction(account=current_user,
                                  change=application.actual_hours * activity.reward_rate,
                                  feedback_id=new_feedback)
    new_feedback.transaction = new_transaction
    db.session.add(new_transaction)

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    all_feedback_in = all(application.feedback is not None
                          for activity in project.activities
                          for application in activity.applications)
    if all_feedback_in:
        mods = [*project.moderators, project.creator]
        notify_all(mods, NotificationType.all_feedback_in, {
            'project_id': project.id,
        })

    out_schema = FeedbackSchema()
    return out_schema.jsonify(new_feedback)
