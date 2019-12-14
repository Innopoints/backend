from datetime import datetime
from enum import Enum, auto

from innopoints.extensions import db

class StockChangeStatus(Enum):
    """Represents a status of product variety stock change"""
    carried_out = auto()
    pending = auto()
    ready_for_pickup = auto()
    rejected = auto()


class Variety(db.Model):
    """Represents various types of one product"""
    __tablename__ = 'varieties'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(3), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)
    images = db.relationship('ProductImage',
                             cascade='all, delete-orphan')
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan')

    @property
    def amount(self):
        """Return the amount of items of this variety, computed
           from the StockChange instances"""
        return db.session.query(
            db.func.sum(StockChange.amount)
        ).filter(
            StockChange.variety == self,
            StockChange.status != StockChangeStatus.rejected
        ).scalar()


class ProductImage(db.Model):
    """Represents an ordered image for a particular product"""
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    variety_id = db.Column(db.Integer, db.ForeignKey('varieties.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)


class StockChange(db.Model):
    """Represents the change in the amount of variety available"""
    __tablename__ = 'stock_changes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(StockChangeStatus), nullable=False)
    account_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    variety_id = db.Column(db.Integer, db.ForeignKey('varieties.id'), nullable=False)
    transaction = db.relationship('Transaction')


class Color(db.Model):
    """Represents colors of items in the store"""
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(6), nullable=False, unique=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan')
