"""Application views"""

from flask import Blueprint, abort, jsonify, request
from flask.views import MethodView
from werkzeug.exceptions import BadRequestKeyError

from innopoints.models import db, LifetimeStage, Product, Project, Competence

api = Blueprint('api', __name__)  # pylint: disable=invalid-name


@api.route('/projects')
def get_projects():
    """List ongoing or past projects"""
    if not request.is_json:
        abort(400)

    try:
        lifetime = request.json['type']
        page = int(request.json['page'])
        query = request.json['q']
    except (BadRequestKeyError, ValueError):
        abort(400)

    lifetime_stage = LifetimeStage.created if lifetime == 'ongoing' else LifetimeStage.finished

    # yapf: disable
    projects = [{
        'title': project.title,
        'project_url': project.url,
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
            'reward': activity.fixed_reward + activity.working_hours * activity.reward_rate,
        } for activity in project.activities],
    } for project in Project.query.filter_by(lifetime_stage=lifetime_stage).all()]
    # yapf: enable

    return jsonify(projects)


@api.route('/products')
def get_products():
    """List products available in InnoStore"""
    if not request.is_json:
        abort(400)

    try:
        limit = int(request.json['limit'])
        query = request.json['q']
        page = int(request.json['page'])
    except (BadRequestKeyError, ValueError):
        abort(400)

    ordered_query = Product.query.order_by(Product.cost.asc())
    offset_limit_query = ordered_query.offset(limit * (page - 1)).limit(limit)

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
            'background': variety.color + 1,
        } for variety in product.varieties],
    } for product in offset_limit_query.all()]
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

        competence = Competence.query.get(compt_id)
        if not competence:
            abort(404)
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

        competence = Competence.query.get(compt_id)
        if not competence:
            abort(404)
        competence.name = name
        competence.save()
        return jsonify(id=competence.id)

    def delete(self, compt_id):
        """Delete chosen competence"""
        if compt_id is None:
            abort(400)

        competence = Competence.query.get(compt_id)
        if not competence:
            abort(404)

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
