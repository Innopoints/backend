"""The Tag model."""

from innopoints.extensions import db


class Tag(db.Model):
    """Represents tags for grouping projects in the statistics."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
