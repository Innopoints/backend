"""Views delivering statistics.

- GET /statistics/competences
- GET /statistics/hours
- GET /statistics/innopoints
"""

from datetime import datetime

from flask import jsonify, request

from innopoints.blueprints import api
from innopoints.core.helpers import abort, admin_required
from innopoints.core.timezone import tz_aware_now, unix_epoch
from innopoints.extensions import db
from innopoints.models import (
    Account,
    Activity,
    Application,
    Competence,
    Feedback,
    LifetimeStage,
    Project,
    StockChange,
    Transaction,
    feedback_competence,
    project_tags,
)


@api.route('/statistics/competences')
@admin_required
def get_competence_stats():
    """Return the statistics on the developed competences."""
    if 'start_date' in request.args:
        try:
            start_date = datetime.fromisoformat(request.args['start_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if start_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        start_date = unix_epoch

    if 'end_date' in request.args:
        try:
            end_date = datetime.fromisoformat(request.args['end_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if end_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        end_date = tz_aware_now()

    student_groups = request.args.getlist('group')
    project_tag = request.args.get('tag')

    competences = (
        # pylint: disable=bad-continuation
        db.session
            .query(Competence.id.label('competence_id'))
            .join(feedback_competence)
            .join(Feedback)
            .join(Application)
            .join(Activity)
            .join(Project)
            .outerjoin(project_tags)
            .join(Account, Account.email == Application.applicant_email)
            .add_columns(db.func.count(Feedback.application_id).label('amount'))
            .filter(Feedback.time > start_date,
                    Feedback.time < end_date)
            .group_by(Competence.id)
    )

    if student_groups:
        competences = competences.filter(Account.group.in_(student_groups))

    if project_tag is not None:
        competences = competences.filter(project_tags.c.tag_id == project_tag)

    return jsonify([{'id': row[0], 'amount': row[1]} for row in competences.all()])


@api.route('/statistics/hours')
@admin_required
def get_hour_stats():
    """Return the statistics on the volunteering hours."""
    if 'start_date' in request.args:
        try:
            start_date = datetime.fromisoformat(request.args['start_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if start_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        start_date = unix_epoch

    if 'end_date' in request.args:
        try:
            end_date = datetime.fromisoformat(request.args['end_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if end_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        end_date = tz_aware_now()

    student_groups = request.args.getlist('group')
    project_tag = request.args.get('tag')

    hours = (
        # pylint: disable=bad-continuation
        db.session
            .query(db.func.sum(Application.actual_hours))
            .join(Activity)
            .join(Project)
            .outerjoin(project_tags)
            .join(Account, Account.email == Application.applicant_email)
            .filter(Project.lifetime_stage == LifetimeStage.finished)
            .filter(Activity.start_date > start_date,
                    Activity.end_date < end_date)
    )

    if student_groups:
        hours = hours.filter(Account.group.in_(student_groups))

    if project_tag is not None:
        hours = hours.filter(project_tags.c.tag_id == project_tag)

    return jsonify(hours.scalar() or 0)


@api.route('/statistics/innopoints')
@admin_required
def get_innopoint_stats():
    """Return the statistics on the amount of innopoints spent."""
    if 'start_date' in request.args:
        try:
            start_date = datetime.fromisoformat(request.args['start_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if start_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        start_date = unix_epoch

    if 'end_date' in request.args:
        try:
            end_date = datetime.fromisoformat(request.args['end_date'])
        except ValueError:
            abort(400, {'message': 'The datetime must be in ISO format with timezone.'})

        if end_date.tzinfo is None:
            abort(400, {'message': 'The timezone must be passed.'})
    else:
        end_date = tz_aware_now()

    student_groups = request.args.getlist('group')

    innopoints = (
        # pylint: disable=bad-continuation
        db.session
            .query(db.func.sum(Transaction.change))
            .join(Account)
            .join(StockChange, StockChange.id == Transaction.stock_change_id)
            .filter(StockChange.time > start_date,
                    StockChange.time < end_date)
    )

    if student_groups:
        innopoints = innopoints.filter(Account.group.in_(student_groups))

    return jsonify(-(innopoints.scalar() or 0))
