"""The Color model."""

from innopoints.extensions import db


class Color(db.Model):
    """Represents colors of items in the store."""
    __tablename__ = 'colors'

    value = db.Column(db.String(6), primary_key=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True)
