"""The many-to-many relationship between Activity and Competence."""

from innopoints.extensions import db


activity_competence = db.Table(
    'activity_competence',
    db.Column('activity_id', db.Integer,
              db.ForeignKey('activities.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('competence_id', db.Integer,
              db.ForeignKey('competences.id', ondelete='CASCADE'),
              primary_key=True)
)
