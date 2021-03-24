"""The StockChange model.

Also contains the StockChangeStatus enum."""

from enum import Enum, auto

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db


class StockChangeStatus(Enum):
    """Represents a status of product variety stock change."""
    carried_out = auto()
    pending = auto()
    ready_for_pickup = auto()
    rejected = auto()


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
    account = db.relationship('Account',
                              back_populates='stock_changes')
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    variety = db.relationship('Variety',
                              back_populates='stock_changes')
    transaction = db.relationship('Transaction',
                                  uselist=False,
                                  single_parent=True,
                                  back_populates='stock_change')
