"""The Project model.

Also contains the ReviewStatus and LifetimeStage enums."""

from enum import Enum, auto

from innopoints.core.timezone import tz_aware_now
from innopoints.extensions import db
from innopoints.models.activity import Activity


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
    image = db.relationship('StaticFile', back_populates='cover_for')
    creation_time = db.Column(db.DateTime(timezone=True), nullable=False, default=tz_aware_now)
    activities = db.relationship('Activity',
                                 cascade='all, delete-orphan',
                                 passive_deletes=True,
                                 back_populates='project')
    moderators = db.relationship('Account',
                                 secondary='project_moderation',
                                 back_populates='moderated_projects')
    creator_email = db.Column(db.String(128),
                              db.ForeignKey('accounts.email', ondelete='CASCADE'),
                              nullable=False)
    creator = db.relationship('Account',
                              back_populates='created_projects')
    admin_feedback = db.Column(db.String(1024), nullable=True)
    review_status = db.Column(db.Enum(ReviewStatus), nullable=True)
    lifetime_stage = db.Column(db.Enum(LifetimeStage), nullable=False, default=LifetimeStage.draft)
    tags = db.relationship('Tag', secondary='project_tags')

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
