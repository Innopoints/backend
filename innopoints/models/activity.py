"""The Activity model."""

from innopoints.extensions import db

from innopoints.models.application import Application, ApplicationStatus


IPTS_PER_HOUR = 100
DEFAULT_QUESTIONS = ("What did you learn from this volunteering opportunity?",
                     "What could be improved in the organization?")


class Activity(db.Model):
    """Represents a volunteering activity in the project."""
    __tablename__ = 'activities'
    __table_args__ = (
        db.CheckConstraint('working_hours == NULL OR working_hours >= 0',
                           name='working hours are non-negative'),
        db.CheckConstraint('people_required == NULL OR people_required >= 0',
                           name='people required are unset or non-negative'),
        db.CheckConstraint('draft OR working_hours != NULL',
                           name='working hours are not nullable for non-drafts'),
        db.CheckConstraint(f'draft OR (fixed_reward AND working_hours = 1) '
                           f'OR (NOT fixed_reward AND reward_rate = {IPTS_PER_HOUR})',
                           name='reward policy'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(1024), nullable=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id', ondelete='CASCADE'),
                           nullable=False)
    project = db.relationship('Project',
                              back_populates='activities')
    working_hours = db.Column(db.Integer, nullable=True, default=1)
    reward_rate = db.Column(db.Integer, nullable=False, default=IPTS_PER_HOUR)
    fixed_reward = db.Column(db.Boolean, nullable=False, default=False)
    people_required = db.Column(db.Integer, nullable=True)
    telegram_required = db.Column(db.Boolean, nullable=False, default=False)
    competences = db.relationship('Competence',
                                  secondary='activity_competence')
    application_deadline = db.Column(db.DateTime(timezone=True), nullable=True)
    feedback_questions = db.Column(db.ARRAY(db.String(1024)),
                                   nullable=False,
                                   default=DEFAULT_QUESTIONS)
    internal = db.Column(db.Boolean, nullable=False, default=False)
    draft = db.Column(db.Boolean, nullable=False, default=True)
    applications = db.relationship('Application',
                                   cascade='all, delete-orphan',
                                   passive_deletes=True,
                                   back_populates='activity')

    @property
    def dates(self):
        """Return the activity dates as a single JSON object."""
        return {'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat()}

    @property
    def accepted_applications(self):
        """Return the amount of accepted applications."""
        return Application.query.filter_by(activity_id=self.id,
                                           status=ApplicationStatus.approved).count()

    @property
    def vacant_spots(self):
        """Return the amount of vacant spots for the activity."""
        if self.people_required is None:
            return -1

        return self.people_required - self.accepted_applications

    def has_application_from(self, user):
        """Return whether the given user has applied for this activity."""
        application = Application.query.filter_by(applicant=user, activity_id=self.id)
        return db.session.query(application.exists()).scalar()

    @property
    def is_complete(self):
        """Return whether the all the required fields for an activity have been filled out."""
        return (
            self.name is not None
            and not self.name.isspace()
            and self.start_date is not None
            and self.end_date is not None
            and self.start_date <= self.end_date
            and self.working_hours is not None
            and self.reward_rate is not None
            and len(self.competences) in range(1, 4)
        )
