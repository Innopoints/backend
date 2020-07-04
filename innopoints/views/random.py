"""Return a random page.

- GET /random_page
"""

import random

from flask import jsonify

from innopoints.blueprints import api
from innopoints.extensions import db
from innopoints.models import Project, Product


PAGES = [
    '/',
    '/projects',
    '/products',
    '/profile',
    '/dashboard',
    Product,
    Project,
]

@api.route('/random_page')
def get_random_page():
    """Return a random URL on the frontend."""
    random_page = random.choice(PAGES)
    if isinstance(random_page, str):
        return jsonify(url=random_page)

    random_object = random_page.query.order_by(db.func.random()).limit(1).one_or_none()
    if random_object is None:
        return jsonify(url='/')
    return jsonify(url=f'/{random_page.__tablename__}/{random_object.id}')
