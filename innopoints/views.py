"""Application views"""

from datetime import datetime
import os
import mimetypes

import requests
from authlib.integrations.flask_client import OAuth
from authlib.jose.errors import MissingClaimError, InvalidClaimError
from flask import Blueprint, abort, jsonify, request, current_app, url_for, redirect
from flask.views import MethodView
from flask_login import login_user, login_required, logout_user, current_user
from psycopg2.extras import DateRange
from sqlalchemy import or_
import werkzeug
from werkzeug.exceptions import BadRequestKeyError

import innopoints.file_manager_s3 as file_manager
from innopoints.models import (Activity, ApplicationStatus, Account, Competence, LifetimeStage,
                               Variety, Color, Product, Project, StockChange, StockChangeStatus,
                               StaticFile, db)

INNOPOLIS_SSO_BASE = os.environ['INNOPOLIS_SSO_BASE']

sso_config = requests.get(f'{INNOPOLIS_SSO_BASE}/.well-known/openid-configuration').json()

api = Blueprint('api', __name__)

oauth = OAuth()
oauth.register(
    'innopolis_sso',
    server_metadata_url=f'{INNOPOLIS_SSO_BASE}/.well-known/openid-configuration',
    access_token_url=sso_config.get('token_endpoint',
                                    f'{INNOPOLIS_SSO_BASE}/oauth2/token'),
    authorize_url=sso_config.get('authorization_endpoint',
                                 f'{INNOPOLIS_SSO_BASE}/oauth2/authorize'),
    client_kwargs={'scope': 'openid'},
)


ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}
ALLOWED_SIZES = {'XS', 'S', 'M', 'L', 'XL', 'XXL'}


# ----- Projects -----

@api.route('/projects')
def list_projects():
    """List ongoing or past projects"""

    lifetime_stages = {
        'ongoing': LifetimeStage.created,
        'past': LifetimeStage.finished,
    }

    if 'type' not in request.args or request.args['type'] not in lifetime_stages:
        abort(400, {'message': 'A valid project type must be specified: `ongoing` or `past`.'})

    lifetime_stage = lifetime_stages[request.args['type']]

    db_query = Project.query.filter_by(lifetime_stage=lifetime_stage)
    if 'q' in request.args:
        like_query = f'%{request.args["query"]}%'
        db_query = db_query.join(Project.activities)
        or_condition = or_(Project.title.ilike(like_query),
                           Activity.name.ilike(like_query),
                           Activity.description.ilike(like_query))
        db_query = db_query.filter(or_condition).distinct()

    if lifetime_stage == LifetimeStage.finished:
        page = int(request.args.get('page', 1))
        db_query = db_query.order_by(Project.id.desc())
        db_query = db_query.offset(10 * (page - 1)).limit(10)

    projects = []
    for project in db_query.all():
        project_json = {
            'id': project.id,
            'title': project.title,
            'img': project.image_url,
            'creation_time': project.created_at,
            'organizer': project.organizer,
            'activities': [],
        }

        if current_user.is_authenticated:
            project_json['moderators'] = [moderator.email for moderator in project.moderators]

            if current_user.is_admin:
                project_json['review_status'] = project.review_status

        for activity in project.activities:
            accepted = Activity.query.filter_by(activity=activity,
                                                status=ApplicationStatus.approved).count()
            activity_json = {
                'name': activity.name,
                'dates': {
                    'start': activity.start_date,
                    'end': activity.end_date,
                },
                'vacant_spots': activity.people_required - accepted,
                'competences': [comp.id for comp in activity.competences],
            }
            project_json['activities'].append(activity_json)

        projects.append(project_json)

    return jsonify(projects)


@api.route('/projects/drafts')
@login_required
def list_drafts():
    """Return a list of drafts for the logged in user"""
    db_query = Project.query.filter_by(lifetime_stage=LifetimeStage.draft,
                                       creator=current_user)
    return jsonify([
        {
            'id': project.id,
            'title': project.title,
            'creation_time': project.created_at,
        } for project in db_query.all()
    ])


@api.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    # pylint: disable=no-member
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if 'is_draft' not in request.json:
        abort(400, {'message': 'is_draft should be specified.'})

    is_draft = bool(request.json['is_draft'])

    try:
        creator_id = 1  # request.json['creator_id']

        if not is_draft and not request.json['title']:
            abort(400, {'message': 'The title must not be empty.'})

        if not is_draft and not request.json['img']:
            abort(400, {'message': 'The image must be specified.'})

        if not is_draft and not request.json['organizer']:
            abort(400, {'message': 'The organizer must not be empty.'})

        new_project = Project(title=request.json['title'],
                              image_url=request.json['img'],
                              organizer=request.json['organizer'],
                              lifetime_stage=(LifetimeStage.draft if is_draft
                                              else LifetimeStage.ongoing),
                              creator_id=creator_id)
        db.session.add(new_project)

        for activity_data in request.json['activities']:
            if activity_data['has_fixed_rate'] and activity_data.get('work_hours') != 1:
                abort(400, {'message': 'Fixed-rate activities should have work_hours == 1.'})

            try:
                lower_date = datetime.fromisoformat(activity_data['dates']['start'])
                upper_date = datetime.fromisoformat(activity_data['dates']['end'])
                if lower_date > upper_date:
                    abort(400,
                          {'message': 'The start date must not be greater than the end date.'})
            except (TypeError, KeyError):
                if not is_draft:
                    abort(400, {'message': 'Valid dates should be provided.'})
                lower_date = None
                upper_date = None

            if not is_draft and not activity_data.get('name'):
                abort(400, {'message': 'Activities should have a non-empty name.'})

            if not is_draft and not activity_data.get('work_hours'):
                abort(400, {'message': 'Activities should have valid working hours.'})

            if not is_draft and not activity_data.get('reward_rate'):
                abort(400, {'message': 'Activities should have a valid reward rate.'})

            new_activity = Activity(name=activity_data.get('name'),
                                    description=activity_data.get('description'),
                                    start_date=lower_date,
                                    end_date=upper_date,
                                    working_hours=activity_data.get('work_hours'),
                                    fixed_reward=activity_data['has_fixed_rate'],
                                    reward_rate=activity_data.get('reward_rate'),
                                    people_required=activity_data.get('people_required'),
                                    telegram_required=activity_data.get('telegram_required'),
                                    project=new_project)
            db.session.add(new_activity)

            for competence_id in activity_data.get('competences', ()):
                competence = Competence.query.get(competence_id)
                new_activity.competences.append(competence)

    except KeyError as exc:
        db.session.rollback()
        abort(400, {'message': f'Key {exc} not found.'})
    except ValueError as exc:
        db.session.rollback()
        abort(400, {'message': str(exc)})

    db.session.commit()
    return jsonify(id=new_project.id)


class ProjectDetailAPI(MethodView):
    """REST views for a particular instance of a Project model"""

    # pylint: disable=no-self-use

    def get(self, project_id):
        """Get full information about the project"""
        project = Project.query.get_or_404(project_id)
        # yapf: disable
        json_data = {
            'title': project.title,
            'img': project.image_url,
            'creation_time': project.created_at,
            'organizer': project.organizer,
            'review_status': project.review_status.name,
            'lifetime_stage': project.lifetime_stage.name,
            'activities': [{
                'id': activity.id,
                'name': activity.name,
                'description': activity.description,
                'people_required': activity.people_required,
                'accepted_applications': [{
                    'applicant_name': application.applicant.full_name,
                } for application in activity.applications
                                          if application.status == ApplicationStatus.approved],
                'reward_rate': activity.reward_rate,
                'work_hours': activity.working_hours,
                'has_fixed_rate': activity.fixed_reward,
                'existing_application': 'WTF?',  # TODO: fix when we will add the Application
            } for activity in project.activities],
        }
        # yapf: enable
        return jsonify(json_data)

    @login_required  # TODO: check if the user is a project moderator
    def put(self, project_id):
        """Edit the information of the project"""
        project = Project.query.get_or_404(project_id)
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        try:
            project.title = request.get('title', project.title)
            if 'dates' in request.json:
                lower_date = datetime.fromisoformat(request.json['dates']['start'])
                upper_date = datetime.fromisoformat(request.json['dates']['end'])
                dates = DateRange(lower=lower_date, upper=upper_date)
                project.dates = dates
            project.organizer = request.get('organizer', project.organizer)
            project.image_url = request.get('img', project.image_url)
        except (KeyError, ValueError) as exc:
            abort(400, {'message': str(exc)})

        db.session.add(project)  # pylint: disable=no-member
        db.session.commit()
        return jsonify()

    def delete(self, project_id):
        """Delete the project entirely"""
        project = Project.query.get_or_404(project_id)

        db.session.delete(project)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member
        return jsonify()


project_api = ProjectDetailAPI.as_view('project_detail_api')  # pylint: disable=invalid-name
api.add_url_rule('/projects/<int:project_id>',
                 view_func=project_api,
                 methods=('GET', 'PUT', 'DELETE'))


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
    db_query = db_query.order_by(Product.cost.asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    # yapf: disable
    products = [{
        'id': product.id,
        'name': product.name,
        'type': product.type,
        'description': product.description,
        'price': product.cost,
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
