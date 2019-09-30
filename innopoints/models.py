"""Database models"""
# pylint: disable=no-member,too-few-public-methods

from datetime import datetime, date
from enum import Enum, auto

# pylint: disable=import-error
from flask_sqlalchemy import SQLAlchemy
# pylint: enable=import-error

import innopoints.utils.colors as colors
import innopoints.file_manager_s3 as file_manager


IPTS_PER_HOUR = 70

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


class Project(db.Model):
    """Represents an event for which volunteering is required"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    organizer = db.Column(db.String(64), nullable=True)
    admin_feedback = db.Column(db.String(1024), nullable=True)
    review_status = db.Column(db.Enum(ReviewStatus), nullable=True)
    lifetime_stage = db.Column(db.Enum(LifetimeStage),
                               nullable=False,
                               default=LifetimeStage.draft)
    creator_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)

    creator = db.relationship('Account',
                              backref=db.backref('projects',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
    image = db.relationship('StaticFile',
                            backref=db.backref('projects',
                                               lazy=True,
                                               cascade='all, delete-orphan'))

    @property
    def image_url(self):
        """Return an image URL constructed from the ID"""
        return f'/static/{self.image_id}'


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
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    working_hours = db.Column(db.Integer, nullable=True)
    reward_rate = db.Column(db.Integer, nullable=True, default=IPTS_PER_HOUR)
    fixed_reward = db.Column(db.Boolean, nullable=False)
    people_required = db.Column(db.Integer, nullable=False, default=-1)
    telegram_required = db.Column(db.Boolean, nullable=False, default=False)
    application_deadline = db.Column(db.Date, nullable=True)
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
    size = db.Column(db.String(3), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

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
        return sum([
            s_change.amount for s_change in StockChange.query.filter(
                StockChange.variety_id == self.id,
                StockChange.status != StockChangeStatus.rejected).all()
        ]),


class Color(db.Model):
    """Represents colors of items in the store"""
    __tablename__ = 'colors'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(6), nullable=False)

    @property
    def background(self):
        """Returns the background color for an item with the given color."""
        return colors.get_background(self.value)


class Product(db.Model):
    """Product describes an item in the InnoStore that a user may purchase"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
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


class StaticFile(db.Model):
    """Represents the user-uploaded static files"""
    __tablename__ = 'static_files'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    mimetype = db.Column(db.String(255), nullable=False)
    namespace = db.Column(db.String(64), nullable=False)

    project = db.relationship('Project',
                              backref=db.backref('static_files',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))

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
