"""Flask application factory"""

from flask import Flask
from flask_migrate import Migrate

from innopoints.views import api
from innopoints.models import db


def create_app(config='config/prod.py'):
    """Create Flask application with given configuration"""
    app = Flask(__name__, static_folder=None)
    app.config.from_pyfile(config)

    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(api)

    return app
