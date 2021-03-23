"""The StaticFile model."""

from innopoints.extensions import db


class StaticFile(db.Model):
    """Represents the user-uploaded static files."""
    __tablename__ = 'static_files'

    id = db.Column(db.Integer, primary_key=True)
    mimetype = db.Column(db.String(255), nullable=False)
    owner_email = db.Column(db.String(128),
                            db.ForeignKey('accounts.email', ondelete='CASCADE'),
                            nullable=False)
    owner = db.relationship('Account', back_populates='static_files')
    product_image = db.relationship('ProductImage',
                                    uselist=False,
                                    cascade='all, delete-orphan',
                                    passive_deletes=True,
                                    back_populates='image')
    project_file = db.relationship('ProjectFile',
                                   uselist=False,
                                   cascade='all, delete-orphan',
                                   passive_deletes=True)
    cover_for = db.relationship('Project',
                                back_populates='image')
