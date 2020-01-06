"""The Notification model."""

from enum import Enum, auto

from sqlalchemy.dialects.postgresql import JSONB

from innopoints.extensions import db
from innopoints.core.timezone import tz_aware_now


class NotificationType(Enum):
    """Represents various notifications."""
    purchase_status_changed = auto()
    new_arrivals = auto()
    claim_innopoints = auto()
    application_status_changed = auto()
    service = auto()
    manual_transaction = auto()
    project_review_status_changed = auto()
    all_feedback_in = auto()
    added_as_moderator = auto()
    out_of_stock = auto()
    new_purchase = auto()
    project_review_requested = auto()


type_to_group = {
    NotificationType.purchase_status_changed: 'innostore',
    NotificationType.new_arrivals: 'innostore',
    NotificationType.claim_innopoints: 'volunteering',
    NotificationType.application_status_changed: 'volunteering',
    NotificationType.service: 'service',
    NotificationType.manual_transaction: 'service',
    NotificationType.project_review_status_changed: 'project_creation',
    NotificationType.all_feedback_in: 'project_creation',
    NotificationType.added_as_moderator: 'project_creation',
    NotificationType.out_of_stock: 'administration',
    NotificationType.new_purchase: 'administration',
    NotificationType.project_review_requested: 'administration',
}


class Notification(db.Model):
    """Represents a notification about a certain event."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    payload = db.Column(JSONB, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    type = db.Column(db.Enum(NotificationType), nullable=False)
