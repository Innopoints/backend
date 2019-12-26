"""The Notification model."""

from enum import Enum, auto

from innopoints.extensions import db
from innopoints.core.timezone import tz_aware_now


class NotificationType(Enum):
    """Represents various notifications."""
    purchase_status_changed = auto()
    new_arrivals = auto()
    claim_innopoints = auto()
    application_status_changed = auto()
    service = auto()
    project_review_status_changed = auto()
    all_feedback_in = auto()
    out_of_stock = auto()
    new_purchase = auto()
    project_review_requested = auto()
    added_as_moderator = auto()


class Notification(db.Model):
    """Represents a notification about a certain event."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    payload = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    type = db.Column(db.Enum(NotificationType), nullable=False)
