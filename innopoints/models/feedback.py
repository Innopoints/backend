"""The Feedback model."""

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class Feedback(db.Model):
    """Represents a volunteer's feedback on an activity."""
    __tablename__ = 'feedback'

    application_id = db.Column(db.Integer,
                               db.ForeignKey('applications.id', ondelete='CASCADE'),
                               unique=True,
                               primary_key=True)
    application = db.relationship('Application',
                                  back_populates='feedback',
                                  uselist=False,
                                  single_parent=True)
    competences = db.relationship('Competence',
                                  secondary='feedback_competence')
    time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    answers = db.Column(db.ARRAY(db.String(1024)), nullable=False)
    transaction = db.relationship('Transaction',
                                  uselist=False,
                                  single_parent=True,
                                  back_populates='feedback')
