"""The Project, ProjectFile and Tag models."""

from enum import Enum, auto

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db
from innopoints.models import Activity


project_moderation = db.Table(
    'project_moderation',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('account_email', db.String(128),
              db.ForeignKey('accounts.email', ondelete='CASCADE', onupdate='CASCADE'),
              primary_key=True)
)


project_tags = db.Table(
    'project_tags',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tags.id', ondelete='CASCADE'),
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
    finalizing = auto()
    finished = auto()


class Project(db.Model):
    """Represents a project for volunteering."""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('static_files.id'), nullable=True)
    creation_time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    activities = db.relationship('Activity',
                                 cascade='all, delete-orphan',
                                 passive_deletes=True,
                                 backref='project')
    moderators = db.relationship('Account',
                                 secondary=project_moderation,
                                 backref=db.backref('moderated_projects', lazy=True))
    creator_email = db.Column(db.String(128), db.ForeignKey('accounts.email'), nullable=False)
    # property `creator` created with a backref
    admin_feedback = db.Column(db.String(1024), nullable=True)
    review_status = db.Column(db.Enum(ReviewStatus), nullable=True)
    lifetime_stage = db.Column(db.Enum(LifetimeStage), nullable=False, default=LifetimeStage.draft)

    tags = db.relationship('Tag',
                           secondary=project_tags,
                           backref=db.backref('projects', lazy=True))

    files = db.relationship('ProjectFile',
                            cascade='all, delete-orphan',
                            backref='project')

    @property
    def start_date(self):
        """Returns the project start date as the earliest start_time of its activities."""
        return db.session.query(
            db.func.min(Activity.start_date),
        ).filter(
            Activity.project_id == self.id,
        ).scalar()

    @property
    def end_date(self):
        """Returns the project end date as the earliest start_time of its activities."""
        return db.session.query(
            db.func.max(Activity.end_date),
        ).filter(
            Activity.project_id == self.id,
        ).scalar()

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


class Tag(db.Model):
    """Represents tags for grouping projects in the statistics."""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
