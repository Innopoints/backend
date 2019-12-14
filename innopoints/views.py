"""Application views"""

import os
import mimetypes

import requests
from authlib.integrations.flask_client import OAuth
from authlib.jose.errors import MissingClaimError, InvalidClaimError
from flask import Blueprint, abort, jsonify, request, current_app, url_for, redirect
from flask.views import MethodView
from flask_login import login_user, login_required, logout_user, current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import werkzeug
from werkzeug.exceptions import BadRequestKeyError

import innopoints.file_manager_s3 as file_manager
from innopoints.models import (
    Activity,
    Account,
    Color,
    Competence,
    LifetimeStage,
    Product,
    Project,
    Size,
    StaticFile,
    StockChange,
    StockChangeStatus,
    Variety,
    IPTS_PER_HOUR,
    db
)

from innopoints.schemas import (
    ActivitySchema,
    ColorSchema,
    CompetenceSchema,
    ListProjectSchema,
    ProductSchema,
    ProjectSchema,
    SizeSchema,
)

INNOPOLIS_SSO_BASE = os.environ['INNOPOLIS_SSO_BASE']

api = Blueprint('api', __name__)

oauth = OAuth()
oauth.register(
    'innopolis_sso',
    server_metadata_url=f'{INNOPOLIS_SSO_BASE}/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid'},
)


ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}
NO_PAYLOAD = ('', 204)


# ----- Project -----

@api.route('/projects')
def list_projects():
    """List ongoing or past projects."""

    lifetime_stages = {
        'ongoing': LifetimeStage.ongoing,
        'past': LifetimeStage.past,
    }

    try:
        lifetime_stage = lifetime_stages[request.args['type']]
    except KeyError:
        abort(400, {'message': f'A project type must be one of: {", ".join(lifetime_stages)}'})

    db_query = Project.query.filter_by(lifetime_stage=lifetime_stage)
    if 'q' in request.args:
        like_query = f'%{request.args["query"]}%'
        db_query = db_query.join(Project.activities)
        or_condition = or_(Project.title.ilike(like_query),
                           Activity.name.ilike(like_query),
                           Activity.description.ilike(like_query))
        db_query = db_query.filter(or_condition).distinct()

    if lifetime_stage == LifetimeStage.past:
        page = int(request.args.get('page', 1))
        db_query = db_query.order_by(Project.id.desc())
        db_query = db_query.offset(10 * (page - 1)).limit(10)

    exclude = ['review_status', 'moderators']
    if current_user.is_authenticated:
        exclude.remove('moderators')
        if not current_user.is_admin:
            exclude.remove('review_status')

    schema = ListProjectSchema(many=True, exclude=exclude)
    return schema.jsonify(db_query.all())


@api.route('/projects/drafts')
@login_required
def list_drafts():
    """Return a list of drafts for the logged in user."""
    db_query = Project.query.filter_by(lifetime_stage=LifetimeStage.draft,
                                       creator=current_user)
    schema = ListProjectSchema(many=True, exclude=(
        'image_url',
        'organizer',
        'moderators',
        'review_status',
        'activities',
    ))
    return schema.jsonify(db_query.all())


@api.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new draft project."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    in_schema = ProjectSchema(exclude=('id', 'creation_time', 'creator', 'admin_feedback',
                                       'review_status', 'lifetime_stage', 'files'))

    try:
        new_project = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    new_project.lifetime_stage = LifetimeStage.draft
    new_project.creator = current_user
    new_project.moderators.append(current_user)

    try:
        for new_activity in new_project.activities:
            new_activity.project = new_project

        db.session.add(new_project)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = ProjectSchema(exclude=('admin_feedback', 'review_status', 'files', 'image_id'),
                               context={'user': current_user})
    return out_schema.jsonify(new_project)


@api.route('/projects/<int:project_id>/publish', methods=['POST'])
@login_required
def publish_project(project_id):
    """Publish an existing draft project."""

    project = Project.query.get_or_404(project_id)

    if current_user.is_admin or project.creator == current_user:
        project.lifetime_stage = LifetimeStage.ongoing
        db.session.commit()
    else:
        abort(401)

    return NO_PAYLOAD


class ProjectDetailAPI(MethodView):
    """REST views for a particular instance of a Project model."""

    def get(self, project_id):
        """Get full information about the project"""
        project = Project.query.get_or_404(project_id)
        exclude = ['image_id',
                   'files',
                   'moderators',
                   'review_status',
                   'admin_feedback',
                   'activities.applications',
                   'activities.applications.telegram',
                   'activities.applications.comment']

        if current_user.is_authenticated:
            exclude.remove('moderators')
            exclude.remove('activities.applications')
            if current_user.email in project.moderators or current_user.is_admin:
                exclude.remove('review_status')
                exclude.remove('activities.applications.telegram')
                exclude.remove('activities.applications.comment')
                if current_user == project.creator or current_user.is_admin:
                    exclude.remove('admin_feedback')

        schema = ProjectSchema(exclude=exclude, context={'user': current_user})
        return schema.jsonify(project)

    @login_required
    def patch(self, project_id):
        """Edit the information of the project."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user != project.creator:
            abort(401)

        in_schema = ProjectSchema(only=('name', 'image_id', 'organizer', 'moderators'))

        try:
            updated_project = in_schema.load(request.json, instance=project, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_project)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = ProjectSchema(only=('id', 'name', 'image_url', 'organizer', 'moderators'))
        return out_schema.jsonify(updated_project)

    @login_required
    def delete(self, project_id):
        """Delete the project entirely."""
        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user != project.creator:
            abort(401)

        try:
            db.session.delete(project)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


project_api = ProjectDetailAPI.as_view('project_detail_api')
api.add_url_rule('/projects/<int:project_id>',
                 view_func=project_api,
                 methods=('GET', 'PATCH', 'DELETE'))


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


# ----- Product ----- *

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
        like_query = f'%{search_query}%'
        or_condition = or_(Product.name.ilike(like_query),
                           Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition)
    db_query = db_query.order_by(ordering[order].asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    schema = ProductSchema(many=True, exclude=('notifications', 'description'))
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

    # pylint: disable=no-self-use

    def put(self, product_id):
        """Edit the product with the given ID"""
        product = Product.query.get_or_404(product_id)
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        try:
            if request.get('price', 1) <= 0:
                abort(400, {'message': 'The request should be in JSON.'})

            product.name = request.get('name', product.name)
            product.type = request.get('type', product.type)
            product.description = request.get('description', product.description)
            product.price = request.get('price', product.price)
        except (KeyError, ValueError) as exc:
            abort(400, {'message': str(exc)})

        db.session.add(product)  # pylint: disable=no-member
        db.session.commit()
        return jsonify()

    def delete(self, product_id):
        """Delete the product entirely"""
        product = Product.query.get_or_404(product_id)

        db.session.delete(product)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member
        return jsonify()


product_api = ProductDetailAPI.as_view('product_api')
api.add_url_rule('/products/<int:product_id>',
                 view_func=product_api,
                 methods=('PUT', 'DELETE'))


# ----- Variety ----- *

class VarietyAPI(MethodView):
    """REST views for the Variety model"""

    # pylint: disable=no-self-use

    def put(self, var_id):
        """Update the given variety"""
        variety = Variety.query.get_or_404(var_id)

        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        try:
            if 'color' in request.json and Color.query.get(request.json['color']) is None:
                abort(400, {'message', 'Specify a valid color.'})

            if 'size' in request.json and request.json['size'] not in ALLOWED_SIZES:
                abort(400, {'message', 'Specify a valid size: XS, S, M, L, XL, XXL.'})

            if 'images' in request.json and not request.json['images']:
                abort(400, {'message', 'Specify at least one image.'})

            variety.color = request.get('color', variety.color)
            variety.size = request.get('size', variety.size)
            variety.images = request.get('images', variety.images)

            if 'amount' in request.json:
                diff = request.json['amount'] - variety.amount
                if diff != 0:
                    stock = StockChange(amount=diff,
                                        status=StockChangeStatus.carried_out,
                                        account=1,  # to be replaced by the current user
                                        variety=variety)
                    db.session.add(stock)

        except (KeyError, ValueError) as exc:
            abort(400, {'message': str(exc)})

        db.session.add(variety)  # pylint: disable=no-member
        db.session.commit()
        return jsonify()

    def delete(self, var_id):
        """Delete the variety entirely"""
        variety = Variety.query.get_or_404(var_id)

        db.session.delete(variety)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member
        return jsonify()


variety_api = VarietyAPI.as_view('variety_api')
api.add_url_rule('/varieties/<int:var_id>',
                 view_func=variety_api,
                 methods=('PUT', 'DELETE'))


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

def get_mimetype(file: werkzeug.FileStorage) -> str:
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


# ----- Authorization -----

@api.route('/login', methods=['GET'])
def login():
    """Redirect the user to the Innopolis SSO login page"""
    redirect_uri = url_for('api.authorize', _external=True)
    return oauth.innopolis_sso.authorize_redirect(redirect_uri)


@api.route('/authorize')
def authorize():
    """Catch the user after the back-redirect and fetch the essential info"""
    token = oauth.innopolis_sso.authorize_access_token(
        redirect_uri=url_for('api.authorize', _external=True))
    try:
        userinfo = oauth.innopolis_sso.parse_id_token(token)
    except (MissingClaimError, InvalidClaimError):
        return abort(401)

    user = Account.query.get(userinfo['email'])
    if user is None:
        user = Account(email=userinfo['email'],
                       full_name=userinfo['commonname'],
                       university_status=userinfo['role'],
                       is_admin=current_app.config['IS_ADMIN'](userinfo))
        db.session.add(user)
        db.session.commit()

    if user.full_name != userinfo['commonname']:
        user.full_name = userinfo['commonname']

    if user.university_status != userinfo['role']:
        user.university_status = userinfo['role']

    if user.is_admin != current_app.config['IS_ADMIN'](userinfo):
        user.is_admin = current_app.config['IS_ADMIN'](userinfo)

    db.session.commit()

    login_user(user, remember=True)

    return redirect(url_for('api.list_projects'))


@api.route('/logout')
def logout():
    """Log out the currently signed in user"""
    logout_user()
    return '', 204


@api.route('/login_cheat')
def login_cheat():
    """Bypass OAuth"""
    # TODO: remove this
    users = Account.query.all()
    if not users:
        user = Account(email='debug@only.com',
                       full_name='Cheat Account',
                       university_status='hacker',
                       is_admin=True)
        db.session.add(user)
        db.session.commit()
    else:
        user = users[0]
    login_user(user, remember=True)

    return NO_PAYLOAD
