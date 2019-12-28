"""Views related to notifications.

- GET   /notifications
- PATCH /notifications/{notification_id}/read
"""

from flask import abort
from flask_login import login_required, current_user

from innopoints.blueprints import api
from innopoints.extensions import db
from innopoints.models import Notification
from innopoints.schemas import NotificationSchema


@api.route('/notifications')
@login_required
def get_notifications():
    """Gets all notifications of the current user."""
    query = Notification.query.filter_by(recipient_email=current_user.email)
    notifications = query.all()
    schema = NotificationSchema(many=True)
    return schema.jsonify(notifications)

@api.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
@login_required
def read_notification(notification_id):
    """Marks a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_email != current_user.email:
        abort(401, {'message': 'Not your notification'})
    notification.is_read = True
    db.session.add(notification)
    db.session.commit()
    return NotificationSchema().jsonify(notification)
