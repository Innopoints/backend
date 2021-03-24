"""The many-to-many relationship between Feedback and Competence."""

from innopoints.extensions import db


feedback_competence = db.Table(
    'feedback_competence',
    db.Column('feedback_id', db.Integer,
              db.ForeignKey('feedback.application_id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('competence_id', db.Integer,
              db.ForeignKey('competences.id', ondelete='CASCADE'),
              primary_key=True)
)
