"""The ProjectFile model. Not used."""

from innopoints.extensions import db


class ProjectFile(db.Model):
    """Represents the files that can only be accessed by volunteers and moderators
       of a certain project.

       WARNING: this class is currently not used."""
    __tablename__ = 'project_files'

    project_id = db.Column(db.Integer,
                           db.ForeignKey('projects.id', ondelete='CASCADE'),
                           primary_key=True)
    file_id = db.Column(db.Integer,
                        db.ForeignKey('static_files.id', ondelete='CASCADE'),
                        primary_key=True)
