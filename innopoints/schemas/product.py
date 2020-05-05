"""Schema for the Product model."""

from marshmallow import validate

from innopoints.extensions import ma
from innopoints.models import Product


# pylint: disable=missing-docstring

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        ordered = True
        include_relationships = True

    varieties = ma.Nested('VarietySchema', many=True, validate=validate.Length(min=1))
    name = ma.Str(validate=validate.Length(min=1, max=128))
    type = ma.Str(validate=validate.Length(min=1, max=128), allow_none=True)
    description = ma.Str(validate=validate.Length(max=1024))
    price = ma.Int(validate=validate.Range(min=1))
