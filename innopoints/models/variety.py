"""The Variety, ProductImage, StockChange, Color and Size models."""

from enum import Enum, auto

from innopoints.core.timezone import tz_aware_now
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
        #   op.create_index('unique varieties', 'varieties',
        #                   ['product_id',
        #                    sa.text("coalesce(color, '')"),
        #                    sa.text("coalesce(size, '')")],
        #                   unique=True)
        #
        # In downgrade() use:
        #   op.drop_index('unique varieties', 'varieties')
        db.Index('unique varieties',
                 'product_id',
                 db.text("coalesce(color, '')"),
                 db.text("coalesce(size, '')"),
                 unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer,
                           db.ForeignKey('products.id', ondelete='CASCADE'),
                           nullable=False)
    # property `product` created with a backref
    size = db.Column(db.String(3),
                     db.ForeignKey('sizes.value', ondelete='CASCADE'),
                     nullable=True)
    color = db.Column(db.String(6),
                      db.ForeignKey('colors.value', ondelete='CASCADE'),
                      nullable=True)
    images = db.relationship('ProductImage',
                             cascade='all, delete-orphan',
                             passive_deletes=True)
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    back_populates='variety')

    @property
    def amount(self):
        """Return the amount of items of this variety, computed
           from the StockChange instances."""
        return db.session.query(
            db.func.sum(StockChange.amount)
        ).filter(
            StockChange.variety_id == self.id,
            StockChange.status != StockChangeStatus.rejected
        ).scalar() or 0

    @property
    def purchases(self):
        """Return the amount of purchases of this variety, computed
           from the StockChange instances."""
        # pylint: disable=invalid-unary-operand-type
        return -(db.session.query(
            db.func.sum(StockChange.amount)
        ).join(Account).filter(
            StockChange.variety_id == self.id,
            StockChange.status != StockChangeStatus.rejected,
            StockChange.amount < 0,
            ~Account.is_admin
        ).scalar() or 0)


class ProductImage(db.Model):
    """Represents an ordered image for a particular variety of a product."""
    __tablename__ = 'product_images'
    __table_args__ = (
        db.UniqueConstraint('variety_id', 'order',
                            name='unique order indices',
                            deferrable=True,
                            initially='DEFERRED'),
    )

    id = db.Column(db.Integer, primary_key=True)
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    image_id = db.Column(db.Integer,
                         db.ForeignKey('static_files.id', ondelete='CASCADE'),
                         nullable=False)
    order = db.Column(db.Integer,
                      db.CheckConstraint('"order" >= 0', name='non-negative order'),
                      nullable=False)


class StockChange(db.Model):
    """Represents the change in the amount of variety available."""
    __tablename__ = 'stock_changes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    status = db.Column(db.Enum(StockChangeStatus), nullable=False)
    account_email = db.Column(db.String(128),
                              db.ForeignKey('accounts.email', ondelete='CASCADE'),
                              nullable=False)
    # property `account` created with a backref
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    variety = db.relationship('Variety',
                              back_populates='stock_changes')
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
