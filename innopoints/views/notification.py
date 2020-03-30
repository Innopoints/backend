"""Views related to notifications.

- GET   /notifications
- POST  /notifications/subscribe
- PATCH /notifications/{notification_id}/read
"""

import logging

from flask import request
from flask_login import login_required, current_user
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.extensions import db, push
from innopoints.models import Notification
from innopoints.schemas import NotificationSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/notifications')
@login_required
def get_notifications():
    """Gets all notifications of the current user."""
    query = (
        # pylint: disable=bad-continuation
        Notification.query
            .filter_by(recipient_email=current_user.email)
            .order_by(Notification.timestamp.desc())
    )
    if 'unread' in request.args:
        query = query.filter_by(is_read=False)
    return NotificationSchema(many=True).jsonify(query.all())


@api.route('/notifications/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Adds the user's subscription to push notifications."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    new_subscription = request.json

    if 'endpoint' not in new_subscription:
        abort(400, {'message': 'The endpoint must be specified.'})

    if ('keys' not in new_subscription
            or 'auth' not in new_subscription['keys']
            or 'p256dh' not in new_subscription['keys']):
        abort(400, {'message': 'Encryption keys must be specified.'})

    settings = current_user.notification_settings
    settings.update({'subscriptions': settings.get('subscriptions', []) + [request.json]})
    flag_modified(current_user, 'notification_settings')

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
        abort(400, {'message': 'Data integrity violated.'})

    push.send(new_subscription, {
        'title': 'Test Run',
        'body': 'This is how you\'ll see our notifications!',
    })

    return NO_PAYLOAD


# TODO: JUST FOR TESTING. SHOULD NOT PUSH
@api.route('/notify', methods=['GET'])
@login_required
def notify():
    subscriptions = current_user.notification_settings.get('subscriptions', [])
    data = {
        'title': 'Test Notification',
        'body': 'Will you go out with me?'
    }

    for subscription in subscriptions:
        try:
            push.send(subscription, data)
        except:
            continue

    return NO_PAYLOAD


@api.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
@login_required
def read_notification(notification_id):
    """Marks a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_email != current_user.email:
        abort(401)
    notification.is_read = True
    db.session.add(notification)
    db.session.commit()
    return NO_PAYLOAD
