"""The Competence model."""

from innopoints.extensions import db


class Competence(db.Model):
    """Represents volunteers' competences."""
    __tablename__ = 'competences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
