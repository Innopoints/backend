from datetime import datetime

from innopoints.extensions import db


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True,
                                backref='product')
    price = db.Column(db.Integer, nullable=False)
    addition_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')
