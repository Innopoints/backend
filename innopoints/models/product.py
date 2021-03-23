"""The Product model."""

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase."""
    __tablename__ = 'products'
    __table_args__ = __table_args__ = (
        db.UniqueConstraint('name', 'type',
                            name='unique product'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True,
                                back_populates='product')
    price = db.Column(db.Integer,
                      db.CheckConstraint('price >= 0', name='non-negative price'),
                      nullable=False)
    addition_time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)

    def __str__(self):
        """Human-readable representation of a product."""
        if self.type is None:
            return self.name
        return f"'{self.name}' {self.type}"
