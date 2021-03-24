"""The Transaction model."""

from innopoints.extensions import db


class Transaction(db.Model):
    """Represents a change in the innopoints balance for a certain user."""
    __tablename__ = 'transactions'
    __table_args__ = (
        db.CheckConstraint('(stock_change_id IS NULL) OR (feedback_id IS NULL)',
                           name='not(feedback and stock_change)'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_email = db.Column(db.String(128),
                              db.ForeignKey('accounts.email', ondelete='CASCADE'),
                              nullable=False)
    account = db.relationship('Account', back_populates='transactions')
    change = db.Column(db.Integer, nullable=False)
    stock_change_id = db.Column(db.Integer,
                                db.ForeignKey('stock_changes.id', ondelete='SET NULL'),
                                nullable=True)
    stock_change = db.relationship('StockChange',
                                   back_populates='transaction')
    feedback_id = db.Column(db.Integer,
                            db.ForeignKey('feedback.application_id', ondelete='SET NULL'),
                            nullable=True)
    feedback = db.relationship('Feedback',
                               back_populates='transaction')
