"""Database models"""

from datetime import datetime
from enum import Enum, auto

from flask_login import LoginManager
from flask_login.mixins import UserMixin
from flask_sqlalchemy import SQLAlchemy

import innopoints.file_manager_s3 as file_manager


IPTS_PER_HOUR = 70

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'


class ReviewStatus(Enum):
    """Represents the review status of the project"""
    pending = auto()
    approved = auto()
    rejected = auto()


class LifetimeStage(Enum):
    """Represents the project's lifetime stage"""
    draft = auto()
    created = auto()
    finished = auto()


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
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('account_id', db.String(128), db.ForeignKey('accounts.email'), primary_key=True)
)


class Project(db.Model):
    """Represents a project for volunteering"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), nullable=True)
    creation_time = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    # property `activities` created with a backref
    organizer = db.Column(db.String(64), nullable=True)
    creator_id = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    admin_feedback = db.Column(db.String(1024), nullable=True)
    review_status = db.Column(db.Enum(ReviewStatus), nullable=True)
    lifetime_stage = db.Column(db.Enum(LifetimeStage),
                               nullable=False,
                               default=LifetimeStage.draft)
    # property `files` created with a backref

    creator = db.relationship('Account',
                              backref=db.backref('projects',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    image = db.relationship('StaticFile',
                            backref=db.backref('projects',
                                               lazy=True,
                                               cascade='all, delete-orphan'))

    moderators = db.relationship('Account', secondary=project_moderation,
                                 backref=db.backref('moderated_projects',
                                                    lazy=True))

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
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    working_hours = db.Column(db.Integer, nullable=True)
    reward_rate = db.Column(db.Integer, nullable=True, default=IPTS_PER_HOUR)
    fixed_reward = db.Column(db.Boolean, nullable=False)
    people_required = db.Column(db.Integer, nullable=False, default=-1)
    telegram_required = db.Column(db.Boolean, nullable=False, default=False)
    application_deadline = db.Column(db.DateTime, nullable=True)
    feedback_questions = db.Column(db.ARRAY(db.String(1024)), nullable=False)
    # property `competences` created with a backref

    project = db.relationship('Project',
                              backref=db.backref('activities',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))

    @staticmethod
    def clean(data):
        # TODO: finish up
        clean_data = {}
        try:
            clean_data['start_date'] = datetime.fromisoformat(data['dates']['start'])
            clean_data['end_date'] = datetime.fromisoformat(data['dates']['end'])
        except KeyError:
            clean_data['start_date'] = None
            clean_data['end_date'] = None
        except (TypeError, ValueError):
            raise ValueError('Invalid value provided for date.')

        if (None not in (clean_data['start_date'], clean_data['start_date'])
                and clean_data['start_date'] > clean_data['end_date']):
            raise ValueError('Start date is greater than the end date.')

        try:
            clean_data['deadline'] = datetime.fromisoformat(data['application_deadline'])
        except KeyError:
            clean_data['deadline'] = None
        except (TypeError, ValueError):
            raise ValueError('Invalid value provided for date.')

        if data['work_hours'] <= 0:
            raise ValueError('Working hours must be positive.')

        if data['reward_rate'] <= 0:
            raise ValueError('Reward rate must be positive.')

        if data['people_required'] < 0:
            raise ValueError('People required must be non-negative.')


    @property
    def dates(self):
        """Return the activity dates as a single JSON object"""
        return {'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()}

    @property
    def vacant_spots(self):
        """Return the amount of vacant spots for the activity"""
        accepted = Application.query.filter_by(activity=self,
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
    # property `moderated_projects` created with a backref
    # property `stock_changes` created with a backref
    # property `transactions` created with a backref
    # property `notifications` created with a backref

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
    applicant_id = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    comment = db.Column(db.String(1024), nullable=False)
    application_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    telegram_username = db.Column(db.String(32), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), nullable=False)
    actual_hours = db.Column(db.Integer, nullable=True)
    # property `report` created with a backref
    # property `feedback` created with a backref

    applicant = db.relationship('Account',
                                backref=db.backref('applications',
                                                   lazy=True,
                                                   cascade='all, delete-orphan'))
    activity = db.relationship('Activity',
                               backref=db.backref('applications',
                                                  lazy=True,
                                                  cascade='all, delete-orphan'))


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=False)
    # property `varieties` created with a backref
    price = db.Column(db.Integer, nullable=False)
    addition_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Variety(db.Model):
    """Represents various types of one product"""
    __tablename__ = 'varieties'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(3), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)
    # property `images` created with a backref
    # property `stock_changes` created with a backref

    product = db.relationship('Product',
                              backref=db.backref('varieties',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    color = db.relationship('Color',
                            backref=db.backref('products',
                                               lazy=True,
                                               cascade='all, delete-orphan'))

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

    variety = db.relationship('Variety',
                              backref=db.backref('images',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))

    image = db.relationship('StaticFile')


class StockChange(db.Model):
    """Represents the change in the amount of variety available"""
    __tablename__ = 'stock_changes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(StockChangeStatus), nullable=False)
    account_id = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    variety_id = db.Column(db.Integer, db.ForeignKey('varieties.id'), nullable=False)

    account = db.relationship('Account',
                              backref=db.backref('stock_changes',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    variety = db.relationship('Variety',
                              backref=db.backref('stock_changes',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))


activity_competence = db.Table(
    'activity_competence',
    db.Column('activity_id', db.Integer, db.ForeignKey('activities.id'), primary_key=True),
    db.Column('competence_id', db.Integer, db.ForeignKey('competences.id'), primary_key=True)
)

feedback_competence = db.Table(
    'feedback_competence',
    db.Column('feedback_id', db.Integer, db.ForeignKey('feedback.id'), primary_key=True),
    db.Column('competence_id', db.Integer, db.ForeignKey('competences.id'), primary_key=True)
)


class Competence(db.Model):
    """Represents volunteers' competences"""
    __tablename__ = 'competences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    activities = db.relationship('Activity',
                                 secondary=activity_competence,
                                 lazy=True,
                                 backref=db.backref('competences', lazy=True))

    feedback = db.relationship('Feedback',
                               secondary=feedback_competence,
                               lazy=True,
                               backref=db.backref('competences', lazy=True))

    def save(self):
        """Save object to database"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete object from database"""
        db.session.delete(self)
        db.session.commit()


class VolunteeringReport(db.Model):
    """Represents a moderator's report about a certain occurence of work
       done by a volunteer"""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    rating = db.Column(db.Integer,
                       db.CheckConstraint('rating <= 5 AND rating >= 1'),
                       nullable=False)
    report = db.Column(db.String(1024), nullable=True)

    application = db.relationship('Application',
                                  uselist=False,
                                  backref=db.backref('report',
                                                     lazy=True,
                                                     cascade='all, delete-orphan'))


class Feedback(db.Model):
    """Represents a volunteer's feedback on an activity"""
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    # property `competences` created with a backref
    answers = db.Column(db.ARRAY(db.String(1024)), nullable=False)

    application = db.relationship('Application',
                                  uselist=False,
                                  backref=db.backref('feedback',
                                                     lazy=True,
                                                     cascade='all, delete-orphan'))


class Transaction(db.Model):
    """Represents a change in the innopoints balance for a certain user"""
    __tablename__ = 'transactions'
    __table_args__ = (
        db.CheckConstraint('(stock_change_id IS NULL) != (feedback_id IS NULL)',
                           name='feedback xor stock_change'),
    )

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    stock_change_id = db.Column(db.Integer, db.ForeignKey('stock_changes.id'), nullable=True)
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=True)

    account = db.relationship('Account',
                              backref=db.backref('transactions',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    stock_change = db.relationship('StockChange')
    feedback = db.relationship('Feedback')


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
    recipient_id = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)

    recipient = db.relationship('Account',
                                backref=db.backref('notifications',
                                                   lazy=True,
                                                   cascade='all, delete-orphan'))
    product = db.relationship('Product')
    project = db.relationship('Project')
    activity = db.relationship('Activity')


class Color(db.Model):
    """Represents colors of items in the store"""
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(6), nullable=True)
    # property `products` created with a backref


class StaticFile(db.Model):
    """Represents the user-uploaded static files"""
    __tablename__ = 'static_files'

    id = db.Column(db.Integer, primary_key=True)
    mimetype = db.Column(db.String(255), nullable=False)
    namespace = db.Column(db.String(64), nullable=False)

    def save(self, file_data):
        """Save object to database"""
        db.session.add(self)
        db.session.commit()
        file_manager.store(file_data, str(self.id), self.namespace)

    def delete(self):
        """Delete object from database"""
        file_manager.delete(str(self.id), self.namespace)
        db.session.delete(self)
        db.session.commit()


class ProjectFile(db.Model):
    """Represents the files that can only be accessed by volunteers and moderators
       of a certain project"""
    __tablename__ = 'project_files'

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), primary_key=True)

    project = db.relationship('Project',
                              backref=db.backref('files',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    file = db.relationship('StaticFile')
