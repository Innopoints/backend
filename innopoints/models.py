"""Database models"""
# pylint: disable=no-member,too-few-public-methods

from datetime import datetime, date
from enum import Enum, auto

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql

db = SQLAlchemy()  # pylint: disable=invalid-name


class ReviewStatus(Enum):
    """Represents review status of the project"""
    pending = auto()
    approved = auto()
    rejected = auto()


class LifetimeStage(Enum):
    """Represents project's lifetime stage"""
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


class Account(db.Model):
    """Represents an account of a logged in user"""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(256), nullable=False)
    # university_status = ???
    university_email = db.Column(db.String(128), nullable=False)
    telegram_username = db.Column(db.String(32))
    is_admin = db.Column(db.Boolean, nullable=False)


class Activity(db.Model):
    """Represents a volunteering activity in the project"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    working_hours = db.Column(db.Integer, nullable=False)
    reward_rate = db.Column(db.Integer, nullable=False)
    fixed_reward = db.Column(db.Boolean, nullable=False)
    people_required = db.Column(db.Integer, nullable=False, default=-1)
    telegram_required = db.Column(db.Boolean, nullable=False)
    application_deadline = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    project = db.relationship('Project',
                              backref=db.backref('activities',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))


class Application(db.Model):
    """Represents a volunteering application"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(1024))
    application_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    telegram_username = db.Column(db.String(32))
    status = db.Column(db.Enum(ApplicationStatus), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    applicant = db.relationship('Account',
                                backref=db.backref('applications',
                                                   lazy=True,
                                                   cascade='all, delete-orphan'))
    activity = db.relationship('Activity',
                               backref=db.backref('applications',
                                                  lazy=True,
                                                  cascade='all, delete-orphan'))


# yapf: disable
# pylint: disable=bad-continuation
activity_competence = db.Table('activity_competence',  # pylint: disable=invalid-name
    db.Column('activity_id', db.Integer, db.ForeignKey('activities.id'), primary_key=True),
    db.Column('competence_id', db.Integer, db.ForeignKey('competences.id'), primary_key=True))
# pylint: enable=bad-continuation
# yapf: enable


class Competence(db.Model):
    """Represents volunteers' competences"""
    __tablename__ = 'competences'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    activities = db.relationship('Activity',
                                 secondary=activity_competence,
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


class Variety(db.Model):
    """Represents various types of one product"""
    __tablename__ = 'varieties'

    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(3), nullable=False)
    color = db.Column(db.String(8), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    product = db.relationship('Product',
                              backref=db.backref('varieties',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))


class Project(db.Model):
    """Represents an event for which volunteering is required"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    organizer = db.Column(db.String(64), nullable=False)
    admin_feedback = db.Column(db.String(1024))
    review_status = db.Column(db.Enum(ReviewStatus), nullable=False, default=ReviewStatus.pending)
    lifetime_stage = db.Column(db.Enum(LifetimeStage),
                               nullable=False,
                               default=LifetimeStage.created)
    creator_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)

    creator = db.relationship('Account',
                              backref=db.backref('projects',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(96), nullable=False)
    type = db.Column(db.String(128))
    description = db.Column(db.String(1024), nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    addition_date = db.Column(db.Date, nullable=False, default=date.today)


class ProductImage(db.Model):
    """Stores the location of the product image"""
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(96), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    variety_id = db.Column(db.Integer, db.ForeignKey('varieties.id'), nullable=False)

    variety = db.relationship('Variety',
                              backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))


class StockChange(db.Model):
    """Represents the change in the amount of variety available"""
    __tablename__ = 'stock_changes'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum(StockChangeStatus), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    variety_id = db.Column(db.Integer, db.ForeignKey('varieties.id'), nullable=False)

    account = db.relationship('Account',
                              backref=db.backref('stock_changes',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    variety = db.relationship('Variety',
                              backref=db.backref('stock_changes',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
