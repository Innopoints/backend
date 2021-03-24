"""The many-to-many relationship between Project and Tag."""

from innopoints.extensions import db


project_tags = db.Table(
    'project_tags',
    db.Column('project_id', db.Integer,
              db.ForeignKey('projects.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tags.id', ondelete='CASCADE'),
              primary_key=True)
)
