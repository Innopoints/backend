"""The Account and Transaction models.

Also contains the function to load the user for the login manager."""

from flask_login.mixins import UserMixin
from sqlalchemy.dialects.postgresql import JSONB

from innopoints.extensions import db, login_manager


DEFAULT_NOTIFICATIONS = {
    'innostore': 'off',
    'volunteering': 'off',
    'project_creation': 'off',
    'administration': 'off',
    'service': 'email',
}

class Account(UserMixin, db.Model):
    """Represents an account of a logged in user."""
    __tablename__ = 'accounts'

    full_name = db.Column(db.String(256), nullable=False)
    group = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(128), primary_key=True)
    telegram_username = db.Column(db.String(32), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False)
    created_projects = db.relationship('Project',
                                       cascade='all, delete-orphan',
                                       backref='creator')
    notification_settings = db.Column(JSONB, nullable=False, default=DEFAULT_NOTIFICATIONS)
    # property `moderated_projects` created with a backref
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    backref='account')
    transactions = db.relationship('Transaction',
                                   cascade='all, delete-orphan',
                                   passive_deletes=True,
                                   backref='account')
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan',
                                   backref='applicant')
    reports = db.relationship('VolunteeringReport',
                              cascade='all, delete-orphan')

    def get_id(self):
        """Return the user's e-mail."""
        return self.email

    @property
    def balance(self):
        """Return the user's innopoints balance."""
        return db.session.query(
            db.func.sum(Transaction.change)
        ).filter(
            Transaction.account_email == self.email
        ).scalar() or 0


@login_manager.user_loader
def load_user(email):
    """Return a user instance by the e-mail."""
    return Account.query.get(email)


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
    # property `account` created with a backref
    change = db.Column(db.Integer, nullable=False)
    stock_change_id = db.Column(db.Integer, db.ForeignKey('stock_changes.id'), nullable=True)
    feedback_id = db.Column(db.Integer,
                            db.ForeignKey('feedback.application_id', ondelete='CASCADE'),
                            nullable=True)
