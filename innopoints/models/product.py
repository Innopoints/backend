"""The Product model."""

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase."""

    __tablename__ = "products"
    __table_args__ = __table_args__ = (
        db.UniqueConstraint("name", "type", name="unique product"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    varieties = db.relationship(
        "Variety", cascade="all, delete-orphan", passive_deletes=True, backref="product"
    )
    price = db.Column(
        db.Integer,
        db.CheckConstraint("price >= 0", name="non-negative price"),
        nullable=False,
    )
    addition_time = db.Column(
        db.DateTime(timezone=True), nullable=False, default=tz_aware_now
    )
