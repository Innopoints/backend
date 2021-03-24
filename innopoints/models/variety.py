"""The Variety model."""

from innopoints.extensions import db
from innopoints.models.account import Account
from innopoints.models.stock_change import StockChange, StockChangeStatus


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
    product = db.relationship('Product', back_populates='varieties')
    size = db.Column(db.String(3),
                     db.ForeignKey('sizes.value', ondelete='CASCADE'),
                     nullable=True)
    color = db.Column(db.String(6),
                      db.ForeignKey('colors.value', ondelete='CASCADE'),
                      nullable=True)
    images = db.relationship('ProductImage',
                             cascade='all, delete-orphan',
                             passive_deletes=True,
                             back_populates='variety')
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
        ).join(StockChange.account).filter(
            StockChange.variety_id == self.id,
            StockChange.status != StockChangeStatus.rejected,
            StockChange.amount < 0,
            ~Account.is_admin
        ).scalar() or 0)
