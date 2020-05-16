"""Views related to notifications.

- GET   /notifications
- POST  /notifications/subscribe
- PATCH /notifications/{notification_id}/read
"""

import logging

from flask import request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from innopoints.blueprints import api
from innopoints.core.helpers import abort, allow_no_json
from innopoints.core.notifications.push import subscribe as subscribe_to_push
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
    new_subscription = request.json

    if 'endpoint' not in new_subscription:
        abort(400, {'message': 'The endpoint must be specified.'})

    if ('keys' not in new_subscription
            or 'auth' not in new_subscription['keys']
            or 'p256dh' not in new_subscription['keys']):
        abort(400, {'message': 'Encryption keys must be specified.'})

    try:
        subscribe_to_push(current_user, new_subscription)
    except IntegrityError:
        abort(400, {'message': 'Data integrity violated.'})

    push.send(new_subscription, {
        'title': 'Test Run',
        'body': 'This is how you\'ll see our notifications!',
    })

    return NO_PAYLOAD


@allow_no_json
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
