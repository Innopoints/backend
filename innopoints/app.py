"""Flask application factory"""

import os
from importlib import import_module

from flask import Flask
from flask_migrate import Migrate

from innopoints.extensions import db, ma, oauth, login_manager
from innopoints.blueprints import all_blueprints


def create_app(config='config/prod.py'):
    """Create Flask application with given configuration"""
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.urandom(16)
    app.config.from_pyfile(config)

    # Import DB models. Flask-SQLAlchemy doesn't do this automatically.
    with app.app_context():
        import_module('innopoints.models')

    # Initialize extensions/add-ons/plugins.
    db.init_app(app)
    Migrate(app, db)
    ma.init_app(app)
    oauth.init_app(app)
    login_manager.init_app(app)

    for blueprint in all_blueprints:
        import_module(blueprint.import_name)
        app.register_blueprint(blueprint)

    return app
