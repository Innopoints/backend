"""Database models"""

from datetime import datetime
from enum import Enum, auto

from flask_login import LoginManager
from flask_login.mixins import UserMixin
from flask_sqlalchemy import SQLAlchemy


IPTS_PER_HOUR = 70
DEFAULT_QUESTIONS = ("What did you learn from this volunteering opportunity?",
                     "What could be improved in the organization?")

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
# TODO: set passive_deletes

class ReviewStatus(Enum):
    """Represents the review status of the project"""
    pending = auto()
    approved = auto()
    rejected = auto()


class LifetimeStage(Enum):
    """Represents the project's lifetime stage"""
    draft = auto()
    ongoing = auto()
    past = auto()


class ApplicationStatus(Enum):
    """Represents volunteering application's status"""
    approved = auto()
    pending = auto()
    rejected = auto()


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


project_moderation = db.Table(
    'project_moderation',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('account_email', db.String(128),
              db.ForeignKey('accounts.email', ondelete='CASCADE', onupdate='CASCADE'),
              primary_key=True)
)


class Project(db.Model):
    """Represents a project for volunteering"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    image_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), nullable=True)
    creation_time = db.Column(db.DateTime, default=datetime.utcnow)
    organizer = db.Column(db.String(128), nullable=True)
    activities = db.relationship('Activity',
                                 cascade='all, delete-orphan',
                                 passive_deletes=True,
                                 backref='project')
    moderators = db.relationship('Account',
                                 secondary=project_moderation,
                                 backref=db.backref('moderated_projects',
                                                    lazy=True))
    creator_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    # property `creator` created with a backref
    admin_feedback = db.Column(db.String(1024), nullable=True)
    review_status = db.Column(db.Enum(ReviewStatus), nullable=True)
    lifetime_stage = db.Column(db.Enum(LifetimeStage), nullable=False)

    files = db.relationship('ProjectFile',
                            cascade='all, delete-orphan',
                            backref='project')
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')

    @property
    def image_url(self):
        """Return an image URL constructed from the ID"""
        if self.image_id is None:
            return None
        return f'/file/{self.image_id}'


class Activity(db.Model):
    """Represents a volunteering activity in the project"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False)
    # property `project` created with a backref
    working_hours = db.Column(db.Integer, nullable=True)
    reward_rate = db.Column(db.Integer, nullable=True, default=IPTS_PER_HOUR)
    fixed_reward = db.Column(db.Boolean, nullable=False)
    people_required = db.Column(db.Integer, nullable=False, default=0)
    telegram_required = db.Column(db.Boolean, nullable=False, default=False)
    # property `competences` created with a backref
    application_deadline = db.Column(db.DateTime, nullable=True)
    feedback_questions = db.Column(db.ARRAY(db.String(1024)),
                                   nullable=False,
                                   default=DEFAULT_QUESTIONS)
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan')
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')

    @property
    def dates(self):
        """Return the activity dates as a single JSON object"""
        # pylint: disable=no-member
        return {'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()}

    @property
    def vacant_spots(self):
        """Return the amount of vacant spots for the activity"""
        accepted = Application.query.filter_by(activity_id=self.id,
                                               status=ApplicationStatus.approved).count()
        return max(self.people_required - accepted, -1)


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
    stock_changes = db.relationship('StockChange',
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    backref='account')
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


class Application(db.Model):
    """Represents a volunteering application"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    applicant_email = db.Column(db.String(128),
                                db.ForeignKey('accounts.email', ondelete='CASCADE'),
                                nullable=False)
    # property `applicant` created with a backref
    activity_id = db.Column(db.Integer,
                            db.ForeignKey('activities.id', ondelete='CASCADE'),
                            nullable=False)
    comment = db.Column(db.String(1024), nullable=True)
    application_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    telegram_username = db.Column(db.String(32), nullable=True)
    status = db.Column(db.Enum(ApplicationStatus), nullable=False)
    actual_hours = db.Column(db.Integer, nullable=True)
    report = db.relationship('VolunteeringReport',
                             uselist=False,
                             cascade='all, delete-orphan')
    feedback = db.relationship('Feedback',
                               uselist=False,
                               cascade='all, delete-orphan')


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    varieties = db.relationship('Variety',
                                cascade='all, delete-orphan',
                                passive_deletes=True,
                                backref='product')
    price = db.Column(db.Integer, nullable=False)
    addition_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notifications = db.relationship('Notification',
                                    cascade='all, delete-orphan')


class Variety(db.Model):
    """Represents various types of one product"""
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
    """Represents an ordered image for a particular product"""
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
    """Represents the change in the amount of variety available"""
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


activity_competence = db.Table(
    'activity_competence',
    db.Column('activity_id', db.Integer,
              db.ForeignKey('activities.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('competence_id', db.Integer,
              db.ForeignKey('competences.id', ondelete='CASCADE'),
              primary_key=True)
)

feedback_competence = db.Table(
    'feedback_competence',
    db.Column('feedback_id', db.Integer,
              db.ForeignKey('feedback.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('competence_id', db.Integer,
              db.ForeignKey('competences.id', ondelete='CASCADE'),
              primary_key=True)
)


class Competence(db.Model):
    """Represents volunteers' competences"""
    __tablename__ = 'competences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)

    activities = db.relationship('Activity',
                                 secondary=activity_competence,
                                 lazy=True,
                                 backref=db.backref('competences', lazy=True))

    feedback = db.relationship('Feedback',
                               secondary=feedback_competence,
                               lazy=True,
                               backref=db.backref('competences', lazy=True))


class VolunteeringReport(db.Model):
    """Represents a moderator's report about a certain occurence of work
       done by a volunteer"""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    rating = db.Column(db.Integer,
                       db.CheckConstraint('rating <= 5 AND rating >= 1'),
                       nullable=False)
    content = db.Column(db.String(1024), nullable=True)


class Feedback(db.Model):
    """Represents a volunteer's feedback on an activity"""
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    # property `competences` created with a backref
    answers = db.Column(db.ARRAY(db.String(1024)), nullable=False)
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


class ProjectFile(db.Model):
    """Represents the files that can only be accessed by volunteers and moderators
       of a certain project"""
    __tablename__ = 'project_files'

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), primary_key=True)
