"""Database models"""

from datetime import datetime
from enum import Enum, auto

from innopoints.extensions import db


# TODO: set passive_deletes


class StockChangeStatus(Enum):
    """Represents a status of product variety stock change"""
    carried_out = auto()
    pending = auto()
    ready_for_pickup = auto()
    rejected = auto()


class NotificationType(Enum):
    """Represents various notifications"""
    purchase_ready = auto()
    new_arrivals = auto()
    claim_ipts = auto()
    apl_accept = auto()
    apl_reject = auto()
    service = auto()
    act_table_reject = auto()
    all_feedback_in = auto()
    out_of_stock = auto()
    new_purchase = auto()
    proj_final_review = auto()



class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan')
    price = db.Column(db.Integer, nullable=False)
    addition_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')


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


class Transaction(db.Model):
    """Represents a change in the innopoints balance for a certain user"""
    __tablename__ = 'transactions'
    __table_args__ = (
        db.CheckConstraint('(stock_change_id IS NULL) != (feedback_id IS NULL)',
                           name='feedback xor stock_change'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    stock_change_id = db.Column(db.Integer, db.ForeignKey('stock_changes.id'), nullable=True)
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=True)


class Notification(db.Model):
    """Represents a notification about a certain event"""
    __tablename__ = 'notifications'
    __table_args__ = (
        db.CheckConstraint('(product_id IS NULL)::INTEGER '
                           '+ (project_id IS NULL)::INTEGER '
                           '+ (activity_id IS NULL)::INTEGER '
                           '< 1',
                           name='not more than 1 related object'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)


class Color(db.Model):
    """Represents colors of items in the store"""
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(6), nullable=False, unique=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan')


class StaticFile(db.Model):
    """Represents the user-uploaded static files"""
    __tablename__ = 'static_files'

    id = db.Column(db.Integer, primary_key=True)
    mimetype = db.Column(db.String(255), nullable=False)
    namespace = db.Column(db.String(64), nullable=False)

    product_image = db.relationship('ProductImage',
                                    uselist=False,
                                    cascade='all, delete-orphan')
    project_file = db.relationship('ProjectFile',
                                   uselist=False,
                                   cascade='all, delete-orphan')
    cover_for = db.relationship('Project',
                                uselist=False)

