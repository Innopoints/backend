from marshmallow import validate

from innopoints.extensions import ma, db
from innopoints.models import Product

class ProductSchema(ma.ModelSchema):
    class Meta:
        model = Product
        ordered = True
        sqla_session = db.session

    varieties = ma.Nested('VarietySchema', many=True)
    name = ma.Str(validate=validate.Length(min=1, max=128))
    type = ma.Str(validate=validate.Length(min=1, max=128), allow_none=True)
    description = ma.Str(validate=validate.Length(max=1024))
    price = ma.Int(validate=validate.Range(min=1))
