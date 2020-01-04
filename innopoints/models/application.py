"""The Application, VolunteeringReport and Feedback models."""

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
    # property `applicant` created with a backref
    activity_id = db.Column(db.Integer,
                            db.ForeignKey('activities.id', ondelete='CASCADE'),
                            nullable=False)
    comment = db.Column(db.String(1024), nullable=True)
    application_time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    telegram_username = db.Column(db.String(32), nullable=True)
    status = db.Column(db.Enum(ApplicationStatus),
                       nullable=False,
                       default=ApplicationStatus.pending)
    actual_hours = db.Column(db.Integer, nullable=True)
    report = db.relationship('VolunteeringReport',
                             uselist=False,
                             cascade='all, delete-orphan')
    feedback = db.relationship('Feedback',
                               uselist=False,
                               cascade='all, delete-orphan')


class VolunteeringReport(db.Model):
    """Represents a moderator's report about a certain occurence of work
       done by a volunteer."""
    __tablename__ = 'reports'
    __table_args__ = (
        db.PrimaryKeyConstraint('application_id', 'reporter_email'),
    )

    application_id = db.Column(db.Integer,
                               db.ForeignKey('applications.id'))
    reporter_email = db.Column(db.String(128),
                               db.ForeignKey('accounts.email', ondelete='CASCADE'),
                               nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    rating = db.Column(db.Integer,
                       db.CheckConstraint('rating <= 5 AND rating >= 1'),
                       nullable=False)
    content = db.Column(db.String(1024), nullable=True)


class Feedback(db.Model):
    """Represents a volunteer's feedback on an activity."""
    __tablename__ = 'feedback'

    application_id = db.Column(db.Integer,
                               db.ForeignKey('applications.id'),
                               unique=True,
                               primary_key=True)
    # property `competences` created with a backref
    time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    answers = db.Column(db.ARRAY(db.String(1024)), nullable=False)
    transaction = db.relationship('Transaction')
