"""Views related to notifications."""

from flask_login import login_required, current_user

from innopoints.blueprints import api
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
