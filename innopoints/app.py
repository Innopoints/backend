"""Flask application factory"""

import os

from flask import Flask

from innopoints.views import api, oauth
from innopoints.models import db, login_manager
from innopoints.schemas import ma


def create_app(config='config/prod.py'):
    """Create Flask application with given configuration"""
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.urandom(16)
    app.config.from_pyfile(config)

    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()

    login_manager.init_app(app)

    app.register_blueprint(api)
    oauth.init_app(app)

    return app
