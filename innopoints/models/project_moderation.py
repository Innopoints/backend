"""The many-to-many relationship between Project and its moderators – Account."""

from innopoints.extensions import db


project_moderation = db.Table(
    'project_moderation',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('account_email', db.String(128),
              db.ForeignKey('accounts.email', ondelete='CASCADE'),
              primary_key=True)
)
