"""The Color model."""

from innopoints.extensions import db


class Size(db.Model):
    """Represents sizes of items in the store."""
    __tablename__ = 'sizes'

    value = db.Column(db.String(3), primary_key=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True)
