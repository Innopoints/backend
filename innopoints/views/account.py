"""Views related to the Account model.

Account:
- GET    /account
- GET    /accounts
- GET    /account/{email}
- PATCH  /account/{email}/balance
- GET    /account/timeline
- GET    /account/{email}/timeline
- GET    /account/notification_settings
- GET    /account/{email}/notification_settings
- POST   /account/{email}/notify
- PATCH  /account/telegram
- PATCH  /account/{email}/telegram
- PATCH  /account/notification_settings
- PATCH  /account/{email}/notification_settings
"""

import logging
import math

from flask import request, jsonify
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.core.sql_hacks import as_row
from innopoints.core.notifications import notify
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
from innopoints.schemas import AccountSchema, TimelineSchema, NotificationSettingsSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


def subquery_to_events(subquery, event_type):
    """Take a subquery that has an 'entry_time' field and output a query
    that packs the rest of the fields into a JSON payload and returns it with the time."""
    payload = db.func.row_to_json(as_row(subquery)).cast(JSONB) - 'entry_time'
    return db.session.query(
        'entry_time',
        db.literal(event_type).label('type'),
        payload.label('payload')
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
                                        'transactions', 'applications', 'reports',
                                        'notification_settings'))
    return out_schema.jsonify(user)


@api.route('/accounts')
@login_required
def list_users():
    """List all user accounts on the website."""
    default_page = 1
    default_limit = 25

    try:
        limit = int(request.args.get('limit', default_limit))
        page = int(request.args.get('page', default_page))
    except ValueError:
        abort(400, {'message': 'Bad query parameters.'})

    db_query = db.session.query(Account.email, Account.full_name)
    count_query = db.session.query(db.func.count(Account.email))
    if 'q' in request.args:
        like_query = f'%{request.args["q"]}%'
        db_query = db_query.filter(
            or_(Account.email.ilike(like_query),
                Account.full_name.ilike(like_query))
        )
        count_query = count_query.filter(
            or_(Account.email.ilike(like_query),
                Account.full_name.ilike(like_query))
        )

    if limit < 1 or page < 1:
        abort(400, {'message': 'Limit and page number must be positive.'})

    db_query = db_query.order_by(Account.email.asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    schema = AccountSchema(many=True, only=('email', 'full_name'))
    return jsonify(pages=math.ceil(count_query.scalar() / limit),
                   data=schema.dump(db_query.all()))


@api.route('/account/<string:email>/balance', methods=['PATCH'])
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

        notify(user.email, NotificationType.manual_transaction, {
            'transaction_id': new_transaction.id,
        })

    return NO_PAYLOAD


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
            .outerjoin(Activity, (Activity.project_id == Project.id)
                               & (Activity.internal)
                               & (Activity.name == 'Moderation'))
            .outerjoin(Application, (Application.activity_id == Activity.id)
                                  & (Application.applicant == user))
            .add_column(Application.id.label('application_id'))
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


@api.route('/account/notification_settings', defaults={'email': None})
@api.route('/account/<email>/notification_settings')
@login_required
def get_notification_settings(email):
    """Get the notification settings of the account.
    If the e-mail is not passed, return own settings."""
    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    out_schema = NotificationSettingsSchema()
    return out_schema.jsonify(user.notification_settings)


@api.route('/account/<email>/notify', methods=['POST'])
def service_notification(email):
    """Sends a custom service notification by the admin to any user."""
    user = Account.query.get_or_404(email)

    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    if not request.json.get('message'):
        abort(400, {'message': 'Specify a valid message.'})

    notification = notify(user.email, NotificationType.service, {
        'message': request.json['message']
    })

    if notification is None:
        abort(500, {'message': 'Error creating notification.'})

    return NO_PAYLOAD


@api.route('/account/telegram', methods=['PATCH'], defaults={'email': None})
@api.route('/account/<email>/telegram', methods=['PATCH'])
@login_required
def change_telegram(email):
    """Change a user's Telegram username.
    If the email is not passed, change own username."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    if 'telegram_username' not in request.json:
        abort(400, {'message': 'The telegram_username field must be passed.'})

    user.telegram_username = request.json['telegram_username']
    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD


@api.route('/account/notification_settings', methods=['PATCH'], defaults={'email': None})
@api.route('/account/<email>/notification_settings', methods=['PATCH'])
@login_required
def change_notification_settings(email):
    """Get the notification settings of the account.
    If the e-mail is not passed, return own settings."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    in_schema = NotificationSettingsSchema()
    try:
        new_notification_settings = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    user.notification_settings = new_notification_settings

    try:
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        log.exception(err)
        abort(400, {'message': 'Data integrity violated.'})

    return NO_PAYLOAD
