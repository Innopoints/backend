"""The Activity and Competence models."""

from innopoints.extensions import db

from .application import Application, ApplicationStatus


IPTS_PER_HOUR = 70
DEFAULT_QUESTIONS = ("What did you learn from this volunteering opportunity?",
                     "What could be improved in the organization?")


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
              db.ForeignKey('feedback.application_id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('competence_id', db.Integer,
              db.ForeignKey('competences.id', ondelete='CASCADE'),
              primary_key=True)
)


class Activity(db.Model):
    """Represents a volunteering activity in the project."""
    __tablename__ = 'activities'
    __table_args__ = (
        db.CheckConstraint(f'(fixed_reward AND working_hours = 1) '
                           f'OR (NOT fixed_reward AND reward_rate = {IPTS_PER_HOUR})',
                           name='reward policy'),
        db.UniqueConstraint('name', 'project_id',
                            name='name is unique inside a project')
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False)
    # property `project` created with a backref
    working_hours = db.Column(db.Integer, nullable=False, default=1)
    reward_rate = db.Column(db.Integer, nullable=False, default=IPTS_PER_HOUR)
    fixed_reward = db.Column(db.Boolean, nullable=False, default=False)
    people_required = db.Column(db.Integer, nullable=False, default=0)
    telegram_required = db.Column(db.Boolean, nullable=False, default=False)
    # property `competences` created with a backref
    application_deadline = db.Column(db.DateTime(timezone=True), nullable=True)
    feedback_questions = db.Column(db.ARRAY(db.String(1024)),
                                   nullable=False,
                                   default=DEFAULT_QUESTIONS)
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan')

    @property
    def dates(self):
        """Return the activity dates as a single JSON object"""
        return {'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()}

    @property
    def vacant_spots(self):
        """Return the amount of vacant spots for the activity"""
        accepted = Application.query.filter_by(activity_id=self.id,
                                               status=ApplicationStatus.approved).count()
        return max(self.people_required - accepted, -1)

    def has_application_from(self, user):
        """Return whether the given user has applied for this activity."""
        application = Application.query.filter_by(applicant=user, activity_id=self.id)
        return db.session.query(application.exists()).scalar()


class Competence(db.Model):
    """Represents volunteers' competences."""
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
