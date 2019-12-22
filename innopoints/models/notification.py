"""The Notification model."""

from enum import Enum, auto

from innopoints.extensions import db


class NotificationType(Enum):
    """Represents various notifications."""
    purchase_ready = auto()
    new_arrivals = auto()
    claim_ipts = auto()
    apl_accept = auto()
    apl_reject = auto()
    service = auto()
    act_table_reject = auto()
    all_feedback_in = auto()
    out_of_stock = auto()
    new_purchase = auto()
    proj_final_review = auto()


class Notification(db.Model):
    """Represents a notification about a certain event."""
    __tablename__ = 'notifications'
    __table_args__ = (
        db.CheckConstraint('(product_id IS NULL)::INTEGER '
                           '+ (project_id IS NULL)::INTEGER '
                           '+ (activity_id IS NULL)::INTEGER '
                           '< 1',
                           name='not more than 1 related object'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
