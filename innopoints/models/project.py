"""The Project and ProjectFile models."""

from datetime import datetime
from enum import Enum, auto

from innopoints.extensions import db


project_moderation = db.Table(
    'project_moderation',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('account_email', db.String(128),
              db.ForeignKey('accounts.email', ondelete='CASCADE', onupdate='CASCADE'),
              primary_key=True)
)


class ReviewStatus(Enum):
    """Represents the review status of the project."""
    pending = auto()
    approved = auto()
    rejected = auto()


class LifetimeStage(Enum):
    """Represents the project's lifetime stage."""
    draft = auto()
    ongoing = auto()
    past = auto()


class Project(db.Model):
    """Represents a project for volunteering."""
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
        """Return an image URL constructed from the ID."""
        if self.image_id is None:
            return None
        return f'/file/{self.image_id}'


class ProjectFile(db.Model):
    """Represents the files that can only be accessed by volunteers and moderators
       of a certain project."""
    __tablename__ = 'project_files'

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), primary_key=True)
