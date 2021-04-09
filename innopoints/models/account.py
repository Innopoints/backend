"""The Account model.

Also contains the function to load the user for the login manager."""

from flask_login.mixins import UserMixin
from sqlalchemy.dialects.postgresql import JSONB

from innopoints.extensions import db, login_manager
from innopoints.models.notification import NotificationGroup
from innopoints.models.transaction import Transaction


DEFAULT_NOTIFICATIONS = {
    NotificationGroup.innostore: 'off',
    NotificationGroup.volunteering: 'off',
    NotificationGroup.project_creation: 'off',
    NotificationGroup.administration: 'off',
    NotificationGroup.service: 'email',
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
                                       passive_deletes=True,
                                       back_populates='creator')
    notification_settings = db.Column(JSONB, nullable=False, default=DEFAULT_NOTIFICATIONS)
    moderated_projects = db.relationship('Project',
                                         secondary='project_moderation',
                                         back_populates='moderators')
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    back_populates='account')
    transactions = db.relationship('Transaction',
                                   cascade='all, delete-orphan',
                                   passive_deletes=True,
                                   back_populates='account')
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan',
                                   passive_deletes=True,
                                   back_populates='applicant')
    static_files = db.relationship('StaticFile',
                                   cascade='all, delete-orphan',
                                   passive_deletes=True,
                                   back_populates='owner')
    reports = db.relationship('VolunteeringReport',
                              cascade='all, delete-orphan',
                              passive_deletes=True,
                              back_populates='reporter')
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    back_populates='recipient')

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
    return db.session.get(Account, email)
