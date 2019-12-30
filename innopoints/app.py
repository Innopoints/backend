"""Flask application factory."""

from importlib import import_module
import logging.config
import os

from flask import Flask
from flask_migrate import Migrate

from innopoints.extensions import db, ma, cors, oauth, login_manager
from innopoints.blueprints import all_blueprints


def create_app(config='config/prod.py'):
    """Create Flask application with given configuration"""
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'datefmt': '%d/%m %H:%M:%S',
                'format': '[%(asctime)s] [%(levelname)8s] %(message)s (%(name)s:%(lineno)s)',
            }
        },
        'handlers': {
            'stderr': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG',
            },
            'logfile': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': './innopoints.log',
                'formatter': 'default',
                'when': 'W0',  # will start a new file each Monday
                'backupCount': 5,  # will only keep the 5 latest files,
                'level': 'ERROR',
            }
        },
        'loggers': {
            'werkzeug': {
                'handlers': ['stderr'],
                'propagate': False,
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['stderr', 'logfile']
        }
    })

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
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    oauth.init_app(app)
    login_manager.init_app(app)

    for blueprint in all_blueprints:
        import_module(blueprint.import_name)
        app.register_blueprint(blueprint)

    return app
