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
    StaticFile,
    StockChange,
    StockChangeStatus,
    Variety,
    db
)
from innopoints.schemas import (
    ListProjectSchema,
    ProjectSchema,
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
ALLOWED_SIZES = {'XS', 'S', 'M', 'L', 'XL', 'XXL'}
NO_PAYLOAD = ('', 204)


# ----- Projects -----

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
        abort(400, {'message': 'Data integrity violated.'})
        db.session.rollback()

    out_schema = ProjectSchema(exclude=('admin_feedback', 'review_status', 'files', 'image_id'))
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

        db.session.add(updated_project)
        db.session.commit()

        out_schema = ProjectSchema(only=('id', 'name', 'image_url', 'organizer', 'moderators'))
        return out_schema.jsonify(updated_project)

    def delete(self, project_id):
        """Delete the project entirely."""
        project = Project.query.get_or_404(project_id)

        project = Project.query.get_or_404(project_id)
        if not current_user.is_admin and current_user != project.creator:
            abort(401)

        db.session.delete(project)
        db.session.commit()
        return NO_PAYLOAD


project_api = ProjectDetailAPI.as_view('project_detail_api')
api.add_url_rule('/projects/<int:project_id>',
                 view_func=project_api,
                 methods=('GET', 'PATCH', 'DELETE'))


@api.route('/products')
def get_products():
    """List products available in InnoStore"""
    try:
        limit = int(request.args['limit'])
        page = int(request.args['page'])
        query = request.json.get('q')
    except (BadRequestKeyError, ValueError):
        abort(400, {'message': 'Missing required query parameters.'})

    db_query = Product.query
    if query is not None:
        like_query = f'%{query}%'
        or_condition = or_(Product.name.ilike(like_query), Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition)
    db_query = db_query.order_by(Product.price.asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    # yapf: disable
    products = [{
        'id': product.id,
        'name': product.name,
        'type': product.type,
        'description': product.description,
        'price': product.price,
        'varieties': [{
            'color': Color.query.get(variety.color),
            'cover_images': [image.url for image in variety.images],
            'background': Color.query.get(variety.color).background,
            'amount': product.amount,
        } for variety in product.varieties],
    } for product in db_query.all()]
    # yapf: enable

    return jsonify(products)


@api.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    # pylint: disable=no-member
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    try:
        if request.json['price'] <= 0:
            abort(400, {'message': 'The price must be strictly positive.'})

        new_product = Product(name=request.json['name'],
                              type=request.json['type'],
                              description=request.json['description'],
                              price=request.json['price'])
        db.session.add(new_product)

        for variety_data in request.json['varieties']:
            if Color.query.get(variety_data['color']) is None:
                abort(400, {'message', 'Specify a valid color.'})

            if variety_data.get('size') not in ALLOWED_SIZES:
                abort(400, {'message', 'Specify a valid size: XS, S, M, L, XL, XXL.'})

            if not variety_data['images']:
                abort(400, {'message', 'Specify at least one image.'})

            new_variety = Variety(color=variety_data['color'],
                                  size=variety_data.get('size'),
                                  images=variety_data['images'],
                                  product=new_product)
            db.session.add(new_variety)

            stock = StockChange(amount=variety_data['amount'],
                                status=StockChangeStatus.carried_out,
                                account=1,  # to be replaced by the current user
                                variety=new_variety)
            db.session.add(stock)

    except (KeyError, ValueError) as exc:
        db.session.rollback()
        abort(400, {'message': str(exc)})

    db.session.commit()
    return jsonify(id=new_product.id)


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


product_api = ProductDetailAPI.as_view('product_api')  # pylint: disable=invalid-name
api.add_url_rule('/products/<int:product_id>',
                 view_func=product_api,
                 methods=('PUT', 'DELETE'))


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


variety_api = VarietyAPI.as_view('variety_api')  # pylint: disable=invalid-name
api.add_url_rule('/varieties/<int:var_id>',
                 view_func=variety_api,
                 methods=('PUT', 'DELETE'))


class CompetenceAPI(MethodView):
    """REST views for Competence model"""

    # pylint: disable=no-self-use

    def get(self, compt_id):
        """Get info on chosen competence"""
        if compt_id is None:
            competences = [{'id': compt.id, 'name': compt.name} for compt in Competence.query.all()]
            return jsonify(competences)

        competence = Competence.query.get_or_404(compt_id)
        return jsonify({'name': competence.name})

    def post(self):
        """Create new competence"""
        if not request.is_json:
            abort(400)

        try:
            name = request.json['name']
        except BadRequestKeyError:
            abort(400)

        new_competence = Competence(name=name)
        new_competence.save()
        return jsonify(id=new_competence.id)

    def put(self, compt_id):
        """Update (change) chosen competence"""
        if compt_id is None or not request.is_json:
            abort(400)

        try:
            name = request.json['name']
        except BadRequestKeyError:
            abort(400)

        competence = Competence.query.get_or_404(compt_id)
        competence.name = name
        competence.save()
        return jsonify(id=competence.id)

    def delete(self, compt_id):
        """Delete chosen competence"""
        if compt_id is None:
            abort(400)

        competence = Competence.query.get_or_404(compt_id)
        competence.delete()
        return jsonify()


competence_api = CompetenceAPI.as_view('competence_api')  # pylint: disable=invalid-name
api.add_url_rule('/competences',
                 defaults={'compt_id': None},
                 view_func=competence_api,
                 methods=('GET', ))
api.add_url_rule('/competences', view_func=competence_api, methods=('POST', ))
api.add_url_rule('/competences/<int:compt_id>',
                 view_func=competence_api,
                 methods=('GET', 'PUT', 'DELETE'))


class StaticFileAPI(MethodView):
    """REST views for StaticFile model"""

    @staticmethod
    def get_mimetype(file: werkzeug.FileStorage) -> str:
        """Return a MIME type of a Flask file object"""
        if file.mimetype:
            return file.mimetype

        return mimetypes.guess_type(file.filename)[0]

    # pylint: disable=no-self-use

    def get(self, file_id):
        """Get the chosen static file"""
        file = StaticFile.query.get_or_404(file_id)
        url = f'{file.namespace}/{file.id}'
        response = current_app.make_response(file_manager.retrieve(url))
        response.headers.set('Content-Type', file.mimetype)
        return response

    def post(self, namespace):
        """Upload a new file to the given namespace"""
        if 'file' not in request.files:
            print('File not found')
            abort(400)

        file = request.files['file']

        if not file.filename:
            print('No filename')
            abort(400)

        mimetype = self.get_mimetype(file)
        if mimetype not in ALLOWED_MIMETYPES:
            print(f'Mimetype "{mimetype}" is not allowed')
            abort(400)

        new_file = StaticFile(mimetype=mimetype, namespace=namespace)
        try:
            new_file.save(file.stream)
        except requests.exceptions.HTTPError as exc:
            print('Upload failed')
            print(exc)
            new_file.delete()
            abort(400)
        return jsonify(id=new_file.id, url=f'/static/{new_file.id}')


static_file_api = StaticFileAPI.as_view('static_file_api')  # pylint: disable=invalid-name
api.add_url_rule('/static/<namespace>', view_func=static_file_api, methods=('POST', ))
api.add_url_rule('/static/<int:file_id>',
                 view_func=static_file_api,
                 methods=('GET', ))


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
