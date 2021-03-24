"""The VolunteeringReport model."""

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class VolunteeringReport(db.Model):
    """Represents a moderator's report about a certain occurence of work
       done by a volunteer."""
    __tablename__ = 'reports'
    __table_args__ = (
        db.PrimaryKeyConstraint('application_id', 'reporter_email'),
    )

    application_id = db.Column(db.Integer,
                               db.ForeignKey('applications.id', ondelete='CASCADE'))
    application = db.relationship('Application', back_populates='reports')
    reporter_email = db.Column(db.String(128),
                               db.ForeignKey('accounts.email', ondelete='CASCADE'),
                               nullable=False)
    reporter = db.relationship('Account', back_populates='reports')
    time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    rating = db.Column(db.Integer,
                       db.CheckConstraint('rating <= 5 AND rating >= 1'),
                       nullable=False)
    content = db.Column(db.String(1024), nullable=True)
