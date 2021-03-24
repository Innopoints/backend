"""The Application model.

Also contains the ApplicationStatus enum."""

from enum import Enum, auto

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class ApplicationStatus(Enum):
    """Represents volunteering application's status."""
    approved = auto()
    pending = auto()
    rejected = auto()


class Application(db.Model):
    """Represents a volunteering application."""
    __tablename__ = 'applications'
    __table_args__ = (
        db.UniqueConstraint('applicant_email', 'activity_id',
                            name='only one application'),
    )

    id = db.Column(db.Integer, primary_key=True)
    applicant_email = db.Column(db.String(128),
                                db.ForeignKey('accounts.email', ondelete='CASCADE'),
                                nullable=False)
    applicant = db.relationship('Account', back_populates='applications')
    activity_id = db.Column(db.Integer,
                            db.ForeignKey('activities.id', ondelete='CASCADE'),
                            nullable=False)
    activity = db.relationship('Activity',
                               uselist=False,
                               single_parent=True,
                               back_populates='applications')
    comment = db.Column(db.String(1024), nullable=True)
    application_time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    telegram_username = db.Column(db.String(32), nullable=True)
    status = db.Column(db.Enum(ApplicationStatus),
                       nullable=False,
                       default=ApplicationStatus.pending)
    actual_hours = db.Column(db.Integer, nullable=False)
    reports = db.relationship('VolunteeringReport',
                              cascade='all, delete-orphan',
                              back_populates='application')
    feedback = db.relationship('Feedback',
                               uselist=False,
                               cascade='all, delete-orphan',
                               passive_deletes=True,
                               back_populates='application')
