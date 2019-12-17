"""Application views"""

import mimetypes

import requests
import werkzeug
from flask import abort, jsonify, request, current_app
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
import innopoints.file_manager_s3 as file_manager
from innopoints.models import (
    Activity,
    Color,
    Competence,
    Product,
    Project,
    Size,
    StaticFile,
    StockChange,
    StockChangeStatus,
    Variety,
    IPTS_PER_HOUR,
)
from innopoints.schemas import (
    ActivitySchema,
    ColorSchema,
    CompetenceSchema,
    ProductSchema,
    SizeSchema,
    VarietySchema,
)


ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}
NO_PAYLOAD = ('', 204)


# ----- Activity -----

@api.route('/projects/<int:project_id>/activity', methods=['POST'])
@login_required
def create_activity(project_id):
    """Create a new activity to an existing project."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin and current_user not in project.moderators:
        abort(401)

    in_schema = ActivitySchema(exclude=('id', 'project', 'applications', 'notifications'))

    try:
        new_activity = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    new_activity.project = project

    try:
        db.session.add(new_activity)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = ActivitySchema(exclude=('notifications', 'existing_application'),
                                context={'user': current_user})
    return out_schema.jsonify(new_activity)


class ActivityAPI(MethodView):
    """REST views for a particular instance of an Activity model."""

    @login_required
    def patch(self, project_id, activity_id):
        """Edit the activity."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user not in project.moderators:
            abort(401)

        activity = Activity.query.get_or_404(activity_id)
        if activity.project != project:
            abort(400, {'message': 'The specified project and activity are unrelated.'})

        in_schema = ActivitySchema(exclude=('id', 'project', 'applications', 'notifications'))

        try:
            updated_activity = in_schema.load(request.json, instance=activity, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        if not activity.fixed_reward and activity.reward_rate != IPTS_PER_HOUR:
            abort(400, {'message': 'The reward rate for hourly activities may not be changed.'})

        try:
            db.session.add(updated_activity)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = ActivitySchema(exclude=('notifications', 'existing_application'),
                                    context={'user': current_user})
        return out_schema.jsonify(updated_activity)

    @login_required
    def delete(self, project_id, activity_id):
        """Delete the activity."""
        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user not in project.moderators:
            abort(401)

        activity = Activity.query.get_or_404(activity_id)
        if activity.project != project:
            abort(400, {'message': 'The specified project and activity are unrelated.'})

        try:
            db.session.delete(activity)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


activity_api = ActivityAPI.as_view('activity_api')
api.add_url_rule('/projects/<int:project_id>/activity/<int:activity_id>',
                 view_func=activity_api,
                 methods=('PATCH', 'DELETE'))


# ----- Product -----

@api.route('/products')
def list_products():
    """List products available in InnoStore."""
    default_limit = 3
    default_page = 1
    default_order = 'time'
    ordering = {
        'time': Product.addition_time,
        'price': Product.price
    }

    try:
        limit = int(request.args.get('limit', default_limit))
        page = int(request.args.get('page', default_page))
        search_query = request.args.get('q')
        order = request.args.get('order', default_order)
    except ValueError:
        abort(400, {'message': 'Bad query parameters.'})

    if limit < 1 or page < 1:
        abort(400, {'message': 'Limit and page number must be positive.'})

    db_query = Product.query
    if search_query is not None:
        # pylint: disable=no-member
        like_query = f'%{search_query}%'
        or_condition = or_(Product.name.ilike(like_query),
                           Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition)
    db_query = db_query.order_by(ordering[order].asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    schema = ProductSchema(many=True, exclude=('notifications', 'description',
                                               'varieties.stock_changes',
                                               'varieties.product',
                                               'varieties.product_id'))
    return schema.jsonify(db_query.all())


@api.route('/products', methods=['POST'])
@login_required
def create_product():
    """Create a new product."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_schema = ProductSchema(exclude=('id', 'addition_time', 'notifications',
                                       'varieties.stock_changes.variety_id',
                                       'varieties.product_id',
                                       'varieties.images.variety_id'),
                              context={'user': current_user})

    try:
        new_product = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        for variety in new_product.varieties:
            variety.product = new_product
            for stock_change in variety.stock_changes:
                stock_change.variety_id = variety.id

        db.session.add(new_product)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = ProductSchema(exclude=('notifications',
                                        'varieties.product_id',
                                        'varieties.product',
                                        'varieties.images.variety_id',
                                        'varieties.images.id',
                                        'varieties.stock_changes'))
    return out_schema.jsonify(new_product)


class ProductDetailAPI(MethodView):
    """REST views for the Product model"""

    @login_required
    def patch(self, product_id):
        """Edit the product."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        if not current_user.is_admin:
            abort(401)
        product = Product.query.get_or_404(product_id)

        in_out_schema = ProductSchema(exclude=('id', 'varieties', 'notifications', 'addition_time'))

        try:
            updated_product = in_out_schema.load(request.json, instance=product, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_product)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        return in_out_schema.jsonify(updated_product)

    @login_required
    def delete(self, product_id):
        """Delete the product."""
        if not current_user.is_admin:
            abort(401)
        product = Product.query.get_or_404(product_id)

        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


product_api = ProductDetailAPI.as_view('product_api')
api.add_url_rule('/products/<int:product_id>',
                 view_func=product_api,
                 methods=('PATCH', 'DELETE'))


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


# ----- Static File -----

def get_mimetype(file: werkzeug.FileStorage) -> str:  # pylint: disable=no-member
    """Return a MIME type of a Flask file object"""
    if file.mimetype:
        return file.mimetype

    return mimetypes.guess_type(file.filename)[0]


@api.route('/file/<namespace>', methods=['POST'])
@login_required
def upload_file(namespace):
    """Upload a file to a given namespace."""
    if 'file' not in request.files:
        abort(400, {'message': 'No file attached.'})

    file = request.files['file']

    if not file.filename:
        abort(400, {'message': 'The file doesn\'t have a name.'})

    mimetype = get_mimetype(file)
    if mimetype not in ALLOWED_MIMETYPES:
        abort(400, {'message': f'Mimetype "{mimetype}" is not allowed'})

    new_file = StaticFile(mimetype=mimetype, namespace=namespace)
    db.session.add(new_file)
    db.session.commit()
    try:
        file_manager.store(file.stream, str(new_file.id), new_file.namespace)
    except requests.exceptions.HTTPError as exc:
        print(exc)  # TODO: replace with proper logging
        db.session.delete(new_file)
        db.session.commit()
        abort(400, {'message': 'Upload failed.'})
    return jsonify(id=new_file.id, url=f'/file/{new_file.id}')


@api.route('/file/<int:file_id>')
def retrieve_file(file_id):
    """Get the chosen static file"""
    file = StaticFile.query.get_or_404(file_id)
    url = f'{file.namespace}/{file.id}'
    file_data = file_manager.retrieve(url)

    if file_data is None:
        abort(404)

    response = current_app.make_response(file_data)
    response.headers.set('Content-Type', file.mimetype)
    return response


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
