from flask_login.mixins import UserMixin

from innopoints.extensions import db, login_manager

class Account(UserMixin, db.Model):
    """Represents an account of a logged in user"""
    __tablename__ = 'accounts'

    full_name = db.Column(db.String(256), nullable=False)
    university_status = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(128), primary_key=True)
    telegram_username = db.Column(db.String(32), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False)
    created_projects = db.relationship('Project',
                                       cascade='all, delete-orphan',
                                       backref='creator')
    # property `moderated_projects` created with a backref
    stock_changes = db.relationship('StockChange')
    transactions = db.relationship('Transaction')
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan',
                                   backref='applicant')


    def get_id(self):
        """Return the user's e-mail"""
        return self.email


@login_manager.user_loader
def load_user(email):
    """Return a user instance by the e-mail"""
    return Account.query.get(email)
