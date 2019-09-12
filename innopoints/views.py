"""Application views"""

from datetime import datetime
import mimetypes

import requests
from flask import Blueprint, abort, jsonify, request, current_app
from flask.views import MethodView
from psycopg2.extras import DateRange
from sqlalchemy import or_
import werkzeug
from werkzeug.exceptions import BadRequestKeyError

import innopoints.file_manager_s3 as file_manager
from innopoints.models import (Activity, ApplicationStatus, Competence, LifetimeStage, Product,
                               Project, StockChange, StockChangeStatus, StaticFile, db)

api = Blueprint('api', __name__)  # pylint: disable=invalid-name
ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}


@api.route('/projects', methods=['GET', 'POST'])
def get_post_projects():
    """List ongoing or past projects"""
    if request.method == 'POST':
        # pylint: disable=no-member
        if not request.is_json:
            abort(400)

        try:
            creator_id = 1  # request.json['creator_id']
            lower_date = datetime.fromisoformat(request.json['dates']['start'])
            upper_date = datetime.fromisoformat(request.json['dates']['end'])
            new_project = Project(title=request.json['title'],
                                  start_date=lower_date,
                                  end_date=upper_date,
                                  image_url=request.json['img'],
                                  organizer=request.json['organizer'],
                                  creator_id=creator_id)
            db.session.add(new_project)

            for activity_data in request.json['activities']:
                new_activity = Activity(name=activity_data['name'],
                                        description=activity_data['description'],
                                        working_hours=activity_data['work_hours'],
                                        fixed_reward=activity_data['has_fixed_rate'],
                                        reward_rate=activity_data['reward_rate'],
                                        people_required=activity_data['people_required'],
                                        telegram_required=activity_data['telegram_required'],
                                        project=new_project)
                db.session.add(new_activity)

        except (KeyError, ValueError):
            db.session.rollback()
            abort(400)

        db.session.commit()
        return jsonify(id=new_project.id)

    try:
        lifetime = request.args['type'].lower()
        if lifetime == 'past':
            page = int(request.args['page'])
        query = request.args.get('q')
    except (BadRequestKeyError, ValueError):
        abort(400)

    lifetime_mapping = {
        'draft': LifetimeStage.draft,
        'ongoing': LifetimeStage.created,
        'past': LifetimeStage.finished,
    }
    try:
        lifetime_stage = lifetime_mapping[lifetime]
    except KeyError:
        abort(400)

    db_query = Project.query.filter_by(lifetime_stage=lifetime_stage)
    if query is not None:
        like_query = f'%{query}%'
        db_query = db_query.join(Project.activities)
        or_condition = or_(Project.title.ilike(like_query), Activity.name.ilike(like_query),
                           Activity.description.ilike(like_query))
        db_query = db_query.filter(or_condition).distinct()
    if lifetime == 'past':
        db_query = db_query.order_by(Project.id.desc())
        db_query = db_query.offset(10 * (page - 1)).limit(10)

    # yapf: disable
    projects = [{
        'id': project.id,
        'title': project.title,
        'img': project.image_url,
        'dates': {
            'start': project.dates.lower,
            'end': project.dates.upper,
        },
        'creation_time': project.created_at,
        'organizer': project.organizer,
        'activities': [{
            'id': activity.id,
            'name': activity.name,
            'vacant_spots': activity.people_required,
            'reward': activity.working_hours * activity.reward_rate,
        } for activity in project.activities],
    } for project in db_query.all()]
    # yapf: enable

    return jsonify(projects)


@api.route('/projects/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_projects(project_id):
    """Get, update and delete projects"""
    project = Project.query.get_or_404(project_id)

    if request.method == 'GET':
        # yapf: disable
        json_data = {
            'id': project.id,
            'title': project.title,
            'dates': {
                'start': project.dates.lower,
                'end': project.dates.upper,
            },
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
                'existing_application': 'WTF?',
            } for activity in project.activities],
        }
        # yapf: enable
        return jsonify(json_data)

    if request.method == 'PUT':
        if not request.is_json:
            abort(400)

        try:
            project.title = request.get('title', project.title)
            if 'dates' in request.json:
                lower_date = datetime.fromisoformat(request.json['dates']['start'])
                upper_date = datetime.fromisoformat(request.json['dates']['end'])
                dates = DateRange(lower=lower_date, upper=upper_date)
                project.dates = dates
            project.organizer = request.get('organizer', project.organizer)
            project.image_url = request.get('img', project.image_url)
        except (KeyError, ValueError):
            abort(400)

        db.session.add(project)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

    db.session.delete(project)  # pylint: disable=no-member
    db.session.commit()  # pylint: disable=no-member
    return jsonify()


@api.route('/products')
def get_products():
    """List products available in InnoStore"""
    try:
        limit = int(request.args['limit'])
        page = int(request.args['page'])
        query = request.json.get('q')
    except (BadRequestKeyError, ValueError):
        abort(400)

    db_query = Product.query
    if query is not None:
        like_query = f'%{query}%'
        or_condition = or_(Product.name.ilike(like_query), Product.description.ilike(like_query))
        db_query = db_query.filter(or_condition)
    db_query = db_query.order_by(Product.cost.asc())
    db_query = db_query.offset(limit * (page - 1)).limit(limit)

    # yapf: disable
    products = [{
        'name': product.name,
        'type': product.type,
        'description': product.description,
        'price': product.cost,
        'url': product.url,
        'varieties': [{
            'color': variety.color,
            'cover_images': [image.url for image in variety.images],
            'background': variety.color,
            'amount': sum([
                s_change.amount for s_change in StockChange.query.filter(
                    StockChange.variety_id == variety.id,
                    StockChange.status != StockChangeStatus.rejected).all()
            ]),
        } for variety in product.varieties],
    } for product in db_query.all()]
    # yapf: enable

    return jsonify(products)


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
        return jsonify(id=new_file.id)


static_file_api = StaticFileAPI.as_view('static_file_api')  # pylint: disable=invalid-name
api.add_url_rule('/static/<namespace>', view_func=static_file_api, methods=('POST', ))
api.add_url_rule('/static/<int:file_id>',
                 view_func=static_file_api,
                 methods=('GET', ))
