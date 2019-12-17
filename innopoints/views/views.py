"""Application views"""

from flask import abort, request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import (
    Color,
    Competence,
    Product,
    Size,
    StockChange,
    StockChangeStatus,
    Variety,
)
from innopoints.schemas import (
    ColorSchema,
    CompetenceSchema,
    SizeSchema,
    VarietySchema,
)

NO_PAYLOAD = ('', 204)


# ----- Variety -----

@api.route('/products/<int:product_id>/variety', methods=['POST'])
@login_required
def create_variety(product_id):
    """Create a new variety."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    product = Product.query.get_or_404(product_id)

    in_schema = VarietySchema(exclude=('id', 'product_id', 'product',
                                       'images.variety_id', 'stock_changes.variety_id',),
                              context={'user': current_user})

    try:
        new_variety = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        new_variety.product = product

        db.session.add(new_variety)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = VarietySchema(exclude=('product_id',
                                        'product',
                                        'images.variety_id',
                                        'images.id'))
    return out_schema.jsonify(new_variety)


class VarietyAPI(MethodView):
    """REST views for a particular instance of the Variety model."""

    @login_required
    def patch(self, product_id, variety_id):
        """Update the given variety."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        if not current_user.is_admin:
            abort(401)

        product = Product.query.get_or_404(product_id)
        variety = Variety.query.get_or_404(variety_id)
        if variety.product != product:
            abort(400, {'message': 'The specified product and variety are unrelated.'})

        in_schema = VarietySchema(exclude=('id', 'product_id', 'stock_changes.variety_id'),
                                  context={'update': True})

        amount = request.json.pop('amount', None)

        try:
            updated_variety = in_schema.load(request.json, instance=variety, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        if amount is not None:
            diff = amount - variety.amount
            if diff != 0:
                stock_change = StockChange(amount=diff,
                                           status=StockChangeStatus.carried_out,
                                           account=current_user,
                                           variety_id=updated_variety.id)
                db.session.add(stock_change)

        try:
            db.session.add(updated_variety)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = VarietySchema(exclude=('product_id', 'stock_changes', 'product', 'purchases'))
        return out_schema.jsonify(updated_variety)

    @login_required
    def delete(self, product_id, variety_id):
        """Delete the variety."""
        if not current_user.is_admin:
            abort(401)

        product = Product.query.get_or_404(product_id)
        variety = Variety.query.get_or_404(variety_id)
        if variety.product != product:
            abort(400, {'message': 'The specified product and variety are unrelated.'})

        try:
            db.session.delete(variety)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


variety_api = VarietyAPI.as_view('variety_api')
api.add_url_rule('/products/<int:product_id>/variety/<int:variety_id>',
                 view_func=variety_api,
                 methods=('PATCH', 'DELETE'))


# ----- Competence -----

@api.route('/competences')
def list_competences():
    """List all of the existing competences."""

    schema = CompetenceSchema(many=True)
    return schema.jsonify(Competence.query.all())


@api.route('/competences', methods=['POST'])
@login_required
def create_competence():
    """Create a new competence."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_schema = CompetenceSchema(exclude=('id',))

    try:
        new_competence = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_competence)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = CompetenceSchema()
    return out_schema.jsonify(new_competence)


class CompetenceAPI(MethodView):
    """REST views for a particular instance of a Competence model."""

    @login_required
    def patch(self, compt_id):
        """Edit the competence."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        competence = Competence.query.get_or_404(compt_id)
        if not current_user.is_admin:
            abort(401)

        in_schema = CompetenceSchema(exclude=('id',))

        try:
            updated_competence = in_schema.load(request.json, instance=competence, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_competence)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = CompetenceSchema()
        return out_schema.jsonify(updated_competence)

    @login_required
    def delete(self, compt_id):
        """Delete the competence."""
        competence = Competence.query.get_or_404(compt_id)

        try:
            db.session.delete(competence)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


competence_api = CompetenceAPI.as_view('competence_api')
api.add_url_rule('/competences/<int:compt_id>',
                 view_func=competence_api,
                 methods=('PATCH', 'DELETE'))


# ----- Color -----

@api.route('/colors')
def list_colors():
    """List all existing colors."""
    schema = ColorSchema(many=True)
    return schema.jsonify(Color.query.all())


@api.route('/colors', methods=['POST'])
@login_required
def create_color():
    """Create a new color."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_out_schema = ColorSchema()

    try:
        new_color = in_out_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_color)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    return in_out_schema.jsonify(new_color)


# ----- Size -----

@api.route('/sizes')
def list_sizes():
    """List all existing sizes."""
    schema = SizeSchema(many=True)
    return schema.jsonify(Size.query.all())


@api.route('/sizes', methods=['POST'])
@login_required
def create_size():
    """Create a new size."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_out_schema = SizeSchema()

    try:
        new_size = in_out_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_size)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    return in_out_schema.jsonify(new_size)
