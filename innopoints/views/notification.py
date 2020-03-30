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
from innopoints.extensions import db
from innopoints.models import Notification
from innopoints.schemas import NotificationSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/notifications')
@login_required
def get_notifications():
    """Gets all notifications of the current user."""
    query = Notification.query.filter_by(recipient_email=current_user.email).order_by(Notification.timestamp.desc())
    if 'unread' in request.args:
        query = query.filter_by(is_read=False)
    return NotificationSchema(many=True).jsonify(query.all())


@api.route('/notifications/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Adds the user's subscription to push notifications."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})
    if 'endpoint' not in request.json:
        abort(400, {'message': 'The endpoint must be specified.'})
    current_user.notification_settings.update({
        'subscriptions': current_user.notification_settings.get('subscriptions', []) + [request.json]
    })
    flag_modified(current_user, 'notification_settings')
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
        abort(400, {'message': 'Data integrity violated.'})
    # TODO: send a notification confirming it's working

    return NO_PAYLOAD


# TODO: JUST FOR TESTING. SHOULD NOT PUSH
@api.route('/notify', methods=['POST'])
def notify():
    """Adds the user's subscription to push notifications."""
    from pywebpush import webpush, WebPushException
    from innopoints.models import Account
    from innopoints.schemas import PayloadSchema
    from flask import copy_current_request_context, current_app
    from json import dumps
    subscriptions = Account.query.get(current_user.email).notification_settings.get('subscriptions', [])
    notification = Notification(
        recipient_email=current_user.email,
        type='service',
        payload=request.json,
    )
    data = PayloadSchema().fill_data(request.json)
    for subscription_info in subscriptions:
        # print(current_app.config["VAPID_PRIVATE_KEY"])
        webpush(subscription_info,
                dumps(data),
                vapid_private_key="53drlqseKG4Ma4lrNG8qo9ann8UnpzyZ7YZQRU52dFI",#current_app.config["VAPID_PRIVATE_KEY"],
                vapid_claims={"sub": "mailto:innopoints@innopolis.university"},
                # content_encoding='aes128gcm',
        )
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
