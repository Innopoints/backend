"""Views related to the Project model.

Project:
- GET    /projects
- GET    /projects/past
- GET    /projects/drafts
- GET    /projects/for_review
- POST   /projects
- PATCH  /projects/{project_id}/publish
- GET    /projects/{project_id}
- PATCH  /projects/{project_id}
- DELETE /projects/{project_id}
- PATCH  /projects/{project_id}/request_review
- PATCH  /projects/{project_id}/finalize
- PATCH  /projects/{project_id}/review_status
"""

import logging
import math

from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.notifications import notify, notify_all
from innopoints.extensions import db
from innopoints.models import (
    Account,
    Activity,
    Application,
    ApplicationStatus,
    LifetimeStage,
    NotificationType,
    Project,
    ReviewStatus,
)
from innopoints.schemas import ProjectSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/projects')
def list_ongoing_projects():
    """List ongoing projects."""
    first_activity = db.func.min(Activity.start_date)
    default_order_by = 'creation_time'
    default_order = 'asc'
    ordering = {
        ('creation_time', 'asc'): Project.creation_time.asc(),
        ('creation_time', 'desc'): Project.creation_time.desc(),
        ('proximity', 'asc'): first_activity.asc(),
        ('proximity', 'desc'): first_activity.desc(),
    }

    db_query = Project.query.filter_by(lifetime_stage=LifetimeStage.ongoing)
    if 'q' in request.args:
        like_query = f'%{request.args["q"]}%'
        db_query = db_query.join(Project.activities).filter(
            or_(Project.name.ilike(like_query),
                Activity.name.ilike(like_query),
                Activity.description.ilike(like_query))
        ).distinct()

    order_by = request.args.get('order_by', default_order_by)
    order = request.args.get('order', default_order)
    if (order_by, order) not in ordering:
        abort(400, {'message': 'Invalid ordering specified.'})

    if order_by == 'proximity':
        db_query = db_query.join(Activity).group_by(Project.id)
    db_query = db_query.order_by(ordering[order_by, order])

    conditional_exclude = ['review_status', 'moderators']
    if current_user.is_authenticated:
        conditional_exclude.remove('moderators')
        if not current_user.is_admin:
            conditional_exclude.remove('review_status')
    exclude = ['admin_feedback', 'files', 'image_id',
               'lifetime_stage', 'admin_feedback']
    activity_exclude = [f'activities.{field}' for field in ('description', 'telegram_required',
                                                            'fixed_reward', 'working_hours',
                                                            'reward_rate', 'people_required',
                                                            'application_deadline', 'project',
                                                            'applications', 'existing_application',
                                                            'feedback_questions')]
    schema = ProjectSchema(many=True, exclude=exclude + activity_exclude + conditional_exclude)
    return schema.jsonify(db_query.all())


@api.route('/projects/past')
def list_past_projects():
    """List past projects."""
    default_page = 1
    default_limit = 12

    db_query = Project.query.filter(or_(Project.lifetime_stage == LifetimeStage.finalizing,
                                        Project.lifetime_stage == LifetimeStage.finished))
    count_query = db.session.query(db.func.count(Project.id)).filter(
        or_(Project.lifetime_stage == LifetimeStage.finalizing,
            Project.lifetime_stage == LifetimeStage.finished)
    )
    if 'q' in request.args:
        like_query = f'%{request.args["q"]}%'
        db_query = db_query.join(Project.activities).filter(
            or_(Project.name.ilike(like_query),
                Activity.name.ilike(like_query),
                Activity.description.ilike(like_query))
        ).distinct()
        count_query = count_query.join(Project.activities).filter(
            or_(Project.name.ilike(like_query),
                Activity.name.ilike(like_query),
                Activity.description.ilike(like_query))
        ).distinct()

    try:
        limit = int(request.args.get('limit', default_limit))
        page = int(request.args.get('page', default_page))
    except ValueError:
        abort(400, {'message': 'Bad query parameters.'})

    if limit < 1 or page < 1:
        abort(400, {'message': 'Limit and page number must be positive.'})

    db_query = db_query.order_by(Project.creation_time.desc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    conditional_exclude = ['review_status', 'moderators']
    if current_user.is_authenticated:
        conditional_exclude.remove('moderators')
        if not current_user.is_admin:
            conditional_exclude.remove('review_status')
    exclude = ['admin_feedback', 'files', 'image_id',
               'lifetime_stage', 'admin_feedback']
    activity_exclude = [f'activities.{field}' for field in ('description', 'telegram_required',
                                                            'fixed_reward', 'working_hours',
                                                            'reward_rate', 'people_required',
                                                            'application_deadline', 'project',
                                                            'applications', 'existing_application',
                                                            'feedback_questions')]
    schema = ProjectSchema(many=True, exclude=exclude + activity_exclude + conditional_exclude)
    return jsonify(pages=math.ceil(count_query.scalar() / limit),
                   data=schema.dump(db_query.all()))


@api.route('/projects/drafts')
@login_required
def list_drafts():
    """Return a list of drafts for the logged in user."""
    db_query = Project.query.filter_by(lifetime_stage=LifetimeStage.draft,
                                       creator=current_user)
    schema = ProjectSchema(many=True, only=('id', 'name', 'creation_time'))
    return schema.jsonify(db_query.all())


@api.route('/projects/for_review')
@login_required
def list_projects_for_review():
    """Return a list of projects pending the administrator's review."""
    if not current_user.is_admin:
        abort(401)

    db_query = Project.query.filter_by(review_status=ReviewStatus.pending)
    schema = ProjectSchema(many=True, only=('id', 'name', 'organizer'))
    return schema.jsonify(db_query.all())


@api.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new draft project."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    in_schema = ProjectSchema(exclude=('id', 'creation_time', 'creator', 'admin_feedback',
                                       'review_status', 'lifetime_stage', 'files'))

    try:
        new_project = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    new_project.lifetime_stage = LifetimeStage.draft
    new_project.creator = current_user
    new_project.moderators.append(current_user)

    for new_activity in new_project.activities:
        new_activity.project = new_project

    moderation = Activity(name='Moderation', internal=True, working_hours=0)
    moderation.project = new_project

    db.session.add(new_project)

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = ProjectSchema(exclude=('admin_feedback', 'review_status', 'files', 'image_id'),
                               context={'user': current_user})
    return out_schema.jsonify(new_project)


@api.route('/projects/<int:project_id>/publish', methods=['PATCH'])
@login_required
def publish_project(project_id):
    """Publish an existing draft project."""

    project = Project.query.get_or_404(project_id)

    if project.lifetime_stage != LifetimeStage.draft:
        abort(400, {'message': 'Only draft projects can be published.'})

    if not current_user.is_admin and project.creator != current_user:
        abort(401)

    if not project.organizer:
        abort(400, {'message': 'The organizer field must not be empty.'})

    external_activity = Activity.query.filter_by(internal=False)
    if not db.session.query(external_activity.exists()).scalar():
        abort(400, {'message': 'The project must have at least one activity.'})

    if not all(len(activity.competences) in range(1, 4) for activity in project.activities):
        abort(400, {'message': 'The activities must have from 1 to 3 competences.'})

    project.lifetime_stage = LifetimeStage.ongoing
    db.session.commit()

    notify_all(project.moderators, NotificationType.added_as_moderator, {
        'project_id': project.id,
        'account_email': current_user.email,
    })

    return NO_PAYLOAD


@api.route('/projects/<int:project_id>/request_review', methods=['PATCH'])
@login_required
def request_review(project_id):
    """Request an admin's review for my project."""

    project = Project.query.get_or_404(project_id)

    if project.lifetime_stage != LifetimeStage.finalizing:
        abort(400, {'message': 'Only projects being finalized can be reviewed.'})

    if current_user != project.creator and not current_user.is_admin:
        abort(401)

    if project.review_status == ReviewStatus.pending:
        abort(400, {'message': 'Project is already under review.'})

    project.review_status = ReviewStatus.pending

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    admins = Account.query.filter_by(is_admin=True).all()
    notify_all(admins, NotificationType.project_review_requested, {
        'project_id': project.id,
    })

    return NO_PAYLOAD


@api.route('/projects/<int:project_id>/finalize', methods=['PATCH'])
@login_required
def finalize_project(project_id):
    """Finalize the project."""
    project = Project.query.get_or_404(project_id)

    if current_user != project.creator and not current_user.is_admin:
        abort(401)

    if project.lifetime_stage != LifetimeStage.ongoing:
        abort(400, {'message': 'Only ongoing projects can be finalized.'})

    project.lifetime_stage = LifetimeStage.finalizing

    moderation = Activity.query.filter_by(project=project,
                                          internal=True,
                                          name='Moderation').one_or_none()
    if moderation is None:
        log.error('The moderation activity couldn\'t be found.')
        abort(500)
    else:
        for moderator in project.moderators:
            moderation.applications.append(
                Application(applicant=moderator, status=ApplicationStatus.approved)
            )

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD


@api.route('/projects/<int:project_id>/review_status', methods=['PATCH'])
@login_required
def review_project(project_id):
    """Review a project in its finalizing stage."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    project = Project.query.get_or_404(project_id)

    if project.lifetime_stage != LifetimeStage.finalizing:
        abort(400, {'message': 'Only projects being finalized can be reviewed.'})

    if not current_user.is_admin:
        abort(401)

    if project.review_status != ReviewStatus.pending:
        abort(400, {'message': 'Can only review projects pending review.'})

    allowed_states = {
        'approved': ReviewStatus.approved,
        'rejected': ReviewStatus.rejected,
    }

    if request.json.get('review_status') not in allowed_states:
        abort(400, {'message': 'Invalid review status specified.'})

    project.review_status = allowed_states[request.json['review_status']]
    if project.review_status == ReviewStatus.approved:
        project.lifetime_stage = LifetimeStage.finished

    if 'admin_feedback' in request.json:
        project.admin_feedback = request.json['admin_feedback']

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    notify_all(project.moderators, NotificationType.project_review_status_changed, {
        'project_id': project.id,
    })
    if project.review_status == ReviewStatus.approved:
        for activity in project.activities:
            for application in activity.applications:
                notify(application.applicant_email, NotificationType.claim_innopoints, {
                    'project_id': project.id,
                    'activity_id': activity.id,
                    'application_id': application.id,
                })

    return NO_PAYLOAD


class ProjectDetailAPI(MethodView):
    """REST views for a particular instance of a Project model."""

    def get(self, project_id):
        """Get full information about the project"""
        project = Project.query.get_or_404(project_id)
        exclude = ['image_id',
                   'files',
                   'moderators',
                   'review_status',
                   'admin_feedback',
                   'activities.applications',
                   'activities.existing_application',
                   'activities.applications.telegram',
                   'activities.applications.comment']

        if current_user.is_authenticated:
            exclude.remove('moderators')
            exclude.remove('activities.applications')
            exclude.remove('activities.existing_application')
            if current_user.email in project.moderators or current_user.is_admin:
                exclude.remove('review_status')
                exclude.remove('activities.applications.telegram')
                exclude.remove('activities.applications.comment')
                if current_user == project.creator or current_user.is_admin:
                    exclude.remove('admin_feedback')

        schema = ProjectSchema(exclude=exclude, context={'user': current_user})
        return schema.jsonify(project)

    @login_required
    def patch(self, project_id):
        """Edit the information of the project."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user != project.creator:
            abort(401)

        if project.lifetime_stage not in (LifetimeStage.draft, LifetimeStage.ongoing):
            abort(400, {'The project may only be edited during its draft and ongoing stages.'})

        in_schema = ProjectSchema(only=('name', 'image_id', 'organizer', 'moderators'))

        try:
            updated_project = in_schema.load(request.json, instance=project, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_project)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = ProjectSchema(only=('id', 'name', 'image_url', 'organizer', 'moderators'))
        return out_schema.jsonify(updated_project)

    @login_required
    def delete(self, project_id):
        """Delete the project entirely."""
        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user != project.creator:
            abort(401)

        try:
            db.session.delete(project)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


project_api = ProjectDetailAPI.as_view('project_detail_api')
api.add_url_rule('/projects/<int:project_id>',
                 view_func=project_api,
                 methods=('GET', 'PATCH', 'DELETE'))
