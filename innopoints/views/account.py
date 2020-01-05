"""Views related to the Account model.

Account:
- GET  /account
- GET  /account/{email}
- POST /account/{email}/balance
- GET  /account/timeline
- GET  /account/{email}/timeline
"""

import logging

from flask import request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.sql_hacks import as_row
from innopoints.extensions import db
from innopoints.models import (
    Account,
    Activity,
    Application,
    Notification,
    NotificationType,
    Product,
    Project,
    StockChange,
    Transaction,
    Variety,
)
from innopoints.schemas import AccountSchema, TimelineSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


def subquery_to_events(subquery, event_type):
    """Take a subquery that has an 'entry_time' field and output a query
    that packs the rest of the fields into a JSON payload and returns it with the time."""
    payload = db.func.row_to_json(as_row(subquery)).cast(JSONB) - 'entry_time'
    return db.session.query(
        'entry_time',
        db.literal(event_type).label('type'),
        payload.cast(db.String).label('payload')
    ).select_from(subquery)


@api.route('/account', defaults={'email': None})
@api.route('/account/<email>')
@login_required
def get_info(email):
    """Get information about an account.
    If the e-mail is not passed, return information about self."""
    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    out_schema = AccountSchema(exclude=('moderated_projects', 'created_projects', 'stock_changes',
                                        'transactions', 'applications', 'reports'))
    return out_schema.jsonify(user)


@api.route('/account/<string:email>/balance', methods=['POST'])
@login_required
def change_balance(email):
    """Change a user's balance."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    if not isinstance(request.json.get('change'), int):
        abort(400, {'message': 'The change in innopoints must be specified as an integer.'})

    user = Account.query.get_or_404(email)
    if request.json['change'] != 0:
        new_transaction = Transaction(account=user,
                                      change=request.json['change'])
        db.session.add(new_transaction)
        try:
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

    return jsonify(balance=user.balance)


@api.route('/account/timeline', defaults={'email': None})
@api.route('/account/<email>/timeline')
@login_required
def get_timeline(email):
    """Get the timeline of the account.
    If the e-mail is not passed, return own timeline."""
    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    # pylint: disable=bad-continuation

    applications = (
        db.session
            .query(Application.id.label('application_id'),
                   Application.status.label('application_status'))
            .add_column(Application.application_time.label('entry_time'))
            .filter_by(applicant=user)
            .join(Activity).add_columns(Activity.name.label('activity_name'),
                                        Activity.id.label('activity_id'))
            .join(Project).add_columns(Project.name.label('project_name'),
                                       Project.id.label('project_id'))
            .add_column((Application.actual_hours * Activity.reward_rate).label('reward'))
    ).subquery()

    purchases = (
        db.session
            .query(StockChange.id.label('stock_change_id'),
                   StockChange.status.label('stock_change_status'),
                   StockChange.time.label('entry_time'))
            .filter_by(account=user)
            .filter(StockChange.amount < 0)
            .join(Variety).join(Product).add_columns(Product.id.label('product_id'),
                                                     Product.name.label('product_name'),
                                                     Product.type.label('product_type'))
    ).subquery()

    promotions = (
        # pylint: disable=unsubscriptable-object
        db.session
            .query(Notification.payload['project_id'].label('project_id'),
                   Notification.timestamp.label('entry_time'))
            .filter_by(recipient_email=user.email, type=NotificationType.added_as_moderator)
            .join(Project,
                  Project.id == Notification.payload.op('->>')('project_id').cast(db.Integer))
            .add_column(Project.name.label('project_name'))
    ).subquery()

    projects = (
        db.session
            .query(Project.id.label('project_id'),
                   Project.name.label('project_name'),
                   Project.review_status,
                   Project.creation_time.label('entry_time'))
            .filter_by(creator=user)
    ).subquery()

    timeline = (subquery_to_events(applications, 'application')
         .union(subquery_to_events(purchases, 'purchase'))
         .union(subquery_to_events(promotions, 'promotion'))
         .union(subquery_to_events(projects, 'project'))
         .order_by(db.desc('entry_time')))

    out_schema = TimelineSchema(many=True)
    return out_schema.jsonify(timeline.all())
