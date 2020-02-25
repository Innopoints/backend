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


class NotificationGroup:
    """Represents notification groups."""

    innostore = "innostore"
    volunteering = "volunteering"
    service = "service"
    project_creation = "project_creation"
    administration = "administration"


type_to_group = {
    NotificationType.purchase_status_changed: NotificationGroup.innostore,
    NotificationType.new_arrivals: NotificationGroup.innostore,
    NotificationType.claim_innopoints: NotificationGroup.volunteering,
    NotificationType.application_status_changed: NotificationGroup.volunteering,
    NotificationType.service: NotificationGroup.service,
    NotificationType.manual_transaction: NotificationGroup.service,
    NotificationType.project_review_status_changed: NotificationGroup.project_creation,
    NotificationType.all_feedback_in: NotificationGroup.project_creation,
    NotificationType.added_as_moderator: NotificationGroup.project_creation,
    NotificationType.out_of_stock: NotificationGroup.administration,
    NotificationType.new_purchase: NotificationGroup.administration,
    NotificationType.project_review_requested: NotificationGroup.administration,
}


class Notification(db.Model):
    """Represents a notification about a certain event."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(
        db.String(128), db.ForeignKey("accounts.email"), nullable=False
    )
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    payload = db.Column(JSONB, nullable=True)
    timestamp = db.Column(
        db.DateTime(timezone=True), nullable=False, default=tz_aware_now
    )
    type = db.Column(db.Enum(NotificationType), nullable=False)
