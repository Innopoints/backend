"""Views related to notifications.

- GET   /notifications
- PATCH /notifications/{notification_id}/read
"""

from flask import request
from flask_login import login_required, current_user

from innopoints.blueprints import api
from innopoints.core.helpers import abort
from innopoints.extensions import db
from innopoints.models import Notification
from innopoints.schemas import NotificationSchema

NO_PAYLOAD = ('', 204)


@api.route('/notifications')
@login_required
def get_notifications():
    """Gets all notifications of the current user."""
    query = Notification.query.filter_by(recipient_email=current_user.email)
    if 'unread' in request.args:
        query = query.filter_by(is_read=False)
    return NotificationSchema(many=True).jsonify(query.all())


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
