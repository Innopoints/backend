"""The Variety, ProductImage, StockChange, Color and Size models."""

from datetime import datetime
from enum import Enum, auto

from innopoints.extensions import db
from .account import Account


class StockChangeStatus(Enum):
    """Represents a status of product variety stock change."""
    carried_out = auto()
    pending = auto()
    ready_for_pickup = auto()
    rejected = auto()


class Variety(db.Model):
    """Represents various types of one product."""
    __tablename__ = 'varieties'
    __table_args__ = (
        # Warning: this index requires a manually written migration.
        # In upgrade() use:
        #   op.create_index('unique_varieties', 'varieties',
        #                   ['product_id',
        #                    sa.text("coalesce(color_value, '')"),
        #                    sa.text("coalesce(size_id, '')")],
        #                   unique=True)
        #
        # In downgrade() use:
        #   op.drop_index('unique_varieties', 'varieties')
        db.Index('unique_varieties',
                 'product_id',
                 db.text("coalesce(color_value, '')"),
                 db.text("coalesce(size_id, '')"),
                 unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer,
                           db.ForeignKey('products.id', ondelete='CASCADE'),
                           nullable=False)
    # property `product` created with a backref
    size_id = db.Column(db.String(3),
                        db.ForeignKey('sizes.value', ondelete='CASCADE'),
                        nullable=True)
    color_value = db.Column(db.String(6),
                            db.ForeignKey('colors.value', ondelete='CASCADE'),
                            nullable=True)
    images = db.relationship('ProductImage',
                             cascade='all, delete-orphan',
                             passive_deletes=True)
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True)

    @property
    def amount(self):
        """Return the amount of items of this variety, computed
           from the StockChange instances."""
        # pylint: disable=no-member
        return db.session.query(
            db.func.sum(StockChange.amount)
        ).filter(
            StockChange.variety_id == self.id,
            StockChange.status != StockChangeStatus.rejected
        ).scalar()

    @property
    def purchases(self):
        """Return the amount of purchases of this variety, computed
           from the StockChange instances."""
        # pylint: disable=no-member
        return -(db.session.query(
            db.func.sum(StockChange.amount)
        ).join(Account).filter(
            StockChange.variety_id == self.id,
            StockChange.status != StockChangeStatus.rejected,
            StockChange.amount < 0,
            Account.email == StockChange.account_email,
            not Account.is_admin
        ).scalar() or 0)


class ProductImage(db.Model):
    """Represents an ordered image for a particular variety of a product."""
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    image_id = db.Column(db.Integer,
                         db.ForeignKey('static_files.id', ondelete='CASCADE'),
                         nullable=False)
    order = db.Column(db.Integer, nullable=False)


class StockChange(db.Model):
    """Represents the change in the amount of variety available."""
    __tablename__ = 'stock_changes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(StockChangeStatus), nullable=False)
    account_email = db.Column(db.String(128),
                              db.ForeignKey('accounts.email', ondelete='CASCADE'),
                              nullable=False)
    # property `account` created with a backref
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    transaction = db.relationship('Transaction', uselist=False)


class Color(db.Model):
    """Represents colors of items in the store."""
    __tablename__ = 'colors'

    value = db.Column(db.String(6), primary_key=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True)


class Size(db.Model):
    """Represents sizes of items in the store."""
    __tablename__ = 'sizes'

    value = db.Column(db.String(3), primary_key=True)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True)
