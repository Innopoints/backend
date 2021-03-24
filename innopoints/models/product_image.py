"""The ProductImage model."""

from innopoints.extensions import db


class ProductImage(db.Model):
    """Represents an ordered image for a particular variety of a product."""
    __tablename__ = 'product_images'
    __table_args__ = (
        db.UniqueConstraint('variety_id', 'order',
                            name='unique order indices',
                            deferrable=True,
                            initially='DEFERRED'),
    )

    id = db.Column(db.Integer, primary_key=True)
    variety_id = db.Column(db.Integer,
                           db.ForeignKey('varieties.id', ondelete='CASCADE'),
                           nullable=False)
    variety = db.relationship('Variety',
                              uselist=False,
                              back_populates='images')
    image_id = db.Column(db.Integer,
                         db.ForeignKey('static_files.id', ondelete='CASCADE'),
                         nullable=False)
    image = db.relationship('StaticFile', back_populates='product_image', uselist=False)
    order = db.Column(db.Integer,
                      db.CheckConstraint('"order" >= 0', name='non-negative order'),
                      nullable=False)
