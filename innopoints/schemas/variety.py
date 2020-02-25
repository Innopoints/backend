"""Schema for the Variety, Color, Size, StockChange and ProductImage models."""

from marshmallow_enum import EnumField
from marshmallow import ValidationError, pre_load, post_dump, pre_dump

from innopoints.extensions import ma, db
from innopoints.models import (
    Variety,
    Color,
    Size,
    StockChange,
    StockChangeStatus,
    ProductImage,
    Product,
)


# pylint: disable=missing-docstring


class VarietySchema(ma.ModelSchema):
    class Meta:
        model = Variety
        ordered = True
        include_fk = True
        sqla_session = db.session

    @pre_load
    def create_stock_change(self, data, **kwargs):  # pylint: disable=unused-argument
        """Convert the integer `amount` property into a stock change."""
        if "stock_changes" in data:
            raise ValidationError(
                "The stock changes are not to be specified explicitly."
            )

        if self.context.get("update", False):
            return data

        if "amount" not in data:
            raise ValidationError("The amount for a variety is not specified.")

        amount = data.pop("amount")
        data["stock_changes"] = [
            {
                "amount": amount,
                "account_email": self.context["user"].email,
                "status": "carried_out",
            }
        ]
        return data

    @pre_load
    def normalize_color(self, data, **kwargs):  # pylint: disable=unused-argument
        """Normalize the color value."""
        if "color" not in data:
            if self.context.get("update", False):
                return data
            raise ValidationError("The color must be specified.")

        if data["color"] is None:
            return data

        if data["color"].startswith("#"):
            data["color"] = data["color"][1:].upper()

        if len(data["color"]) != 6:
            raise ValidationError(
                f'The color value is {len(data["color"])} characters long, 6 expected.'
            )

        return data

    @pre_load
    def enumerate_images(self, data, **kwargs):  # pylint: disable=unused-argument
        """Convert the array of URL strings to an array of image objects with order."""
        if self.context.get("update", False):
            if "images" in data:
                data["images"] = [
                    {"order": idx, "image_id": int(url.split("/")[2])}
                    for (idx, url) in enumerate(data["images"], start=1)
                ]
        else:
            try:
                data["images"] = [
                    {"order": idx, "image_id": int(url.split("/")[2])}
                    for (idx, url) in enumerate(data["images"], start=1)
                ]
            except KeyError:
                raise ValidationError("Images must be specified.")
        return data

    @post_dump
    def format_color(self, data, **kwargs):  # pylint: disable=unused-argument
        """Add a '#' to the color value."""
        if data["color"] is not None:
            data["color"] = "#" + data["color"]
        return data

    @post_dump
    def flatten_images(self, data, **kwargs):  # pylint: disable=unused-argument
        """Convert an array of image objects with order into a flat array of URL strings."""
        if "images" not in data:
            return data

        data["images"] = [
            f'/file/{image["image_id"]}'
            for image in sorted(data["images"], key=lambda x: x["order"])
        ]
        return data

    images = ma.Nested("ProductImageSchema", many=True)
    stock_changes = ma.Nested("StockChangeSchema", many=True)
    amount = ma.Int(dump_only=True)
    purchases = ma.Int(dump_only=True)


class ColorSchema(ma.ModelSchema):
    class Meta:
        model = Color
        ordered = True
        sqla_session = db.session
        exclude = ("varieties",)

    @pre_load
    def normalize_value(self, data, **kwargs):  # pylint: disable=unused-argument
        """Normalize the color value, stripping the '#' and transforming symbols to uppercase."""
        if data["value"].startswith("#"):
            data["value"] = data["value"][1:]

        if len(data["value"]) != 6:
            raise ValidationError(
                f'The color value is {len(data["value"])} characters long, 6 expected.'
            )

        data["value"] = data["value"].upper()

        if not all(char in "0123456789ABCDEF" for char in data["value"]):
            raise ValidationError("The color value contains non-hex symbols.")

        return data

    @post_dump
    def precede_hash(self, data, **kwargs):  # pylint: disable=unused-argument
        """Precede the value of the color with a '#' symbol."""
        data["value"] = "#" + data["value"]
        return data


class SizeSchema(ma.ModelSchema):
    class Meta:
        model = Size
        ordered = True
        sqla_session = db.session
        exclude = ("varieties",)


class StockChangeSchema(ma.ModelSchema):
    class Meta:
        model = StockChange
        ordered = True
        include_fk = True
        sqla_session = db.session

    status = EnumField(StockChangeStatus)
    variety = ma.Nested(VarietySchema, exclude=("stock_changes",))
    account = ma.Nested("AccountSchema", only=("email", "full_name"))
    product = ma.Nested("ProductSchema", only=("id", "name", "type"))

    @pre_dump
    def get_product(self, stock_change, **kwargs):
        stock_change.product = Product.query.get(stock_change.variety.product_id)
        return stock_change


class ProductImageSchema(ma.ModelSchema):
    class Meta:
        model = ProductImage
        ordered = True
        include_fk = True
        sqla_session = db.session
