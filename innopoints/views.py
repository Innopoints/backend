"""Application views"""

from flask import Blueprint, abort, jsonify, request
from werkzeug.exceptions import BadRequestKeyError

from innopoints.models import LifetimeStage, Product, Project

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
