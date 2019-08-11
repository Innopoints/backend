"""Database models"""
# pylint: disable=no-member,too-few-public-methods

from datetime import datetime
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


class Account(db.Model):
    """Represents an account of a logged in user"""
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(256), nullable=False)
    # university_status = ???
    university_email = db.Column(db.String(128), nullable=False)
    telegram_username = db.Column(db.String(32))
    is_admin = db.Column(db.Boolean, nullable=False)


class Project(db.Model):
    """Represents an event for which volunteering is required"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(96), nullable=False)
    image_url = db.Column(db.String(256), nullable=False)
    dates = db.Column(postgresql.DATERANGE, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    organizer = db.Column(db.String(64), nullable=False)
    admin_feedback = db.Column(db.String(1024))
    review_status = db.Column(db.Enum(ReviewStatus), nullable=False)
    lifetime_stage = db.Column(db.Enum(LifetimeStage), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)

    creator = db.relationship('Account',
                              backref=db.backref('projects',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))


class Activity(db.Model):
    """Represents a volunteering activity in the project"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    working_hours = db.Column(db.Integer, nullable=False)
    reward_rate = db.Column(db.Integer, nullable=False)
    fixed_reward = db.Column(db.Integer, nullable=False)
    people_required = db.Column(db.Integer, nullable=False, default=-1)
    telegram_required = db.Column(db.Boolean, nullable=False)
    application_deadline = db.Column(db.Date, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    project = db.relationship('Project',
                              backref=db.backref('activities',
                                                 lazy=True,
                                                 cascade='all, delete-orphan'))
