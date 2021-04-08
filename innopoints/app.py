"""Flask application factory."""

import time
from importlib import import_module
import logging
import logging.config

from flask import Flask
from flask_migrate import Migrate, upgrade
from werkzeug.middleware.proxy_fix import ProxyFix
import psycopg2
import sqlalchemy.exc

from innopoints.extensions import db, ma, mail, oauth, login_manager, push
from innopoints.blueprints import all_blueprints

log = logging.getLogger(__name__)


def create_app(config='config/prod.py'):
    """Create Flask application with given configuration"""
    app = Flask(__name__, static_folder=None)
    app.config.from_pyfile(config)

    # Import DB models. Flask-SQLAlchemy doesn't do this automatically.
    with app.app_context():
        import_module('innopoints.models')

    # Initialize extensions/add-ons/plugins.
    db.init_app(app)
    Migrate(app, db)
    for _ in range(3):
        try:
            with app.app_context():
                db.engine.connect()
            break
        except (RuntimeError, psycopg2.OperationalError, sqlalchemy.exc.OperationalError) as err:
            log.exception(f'Couldn\'t connect to DB. Error: {err.with_traceback(None)}. retrying..')
            time.sleep(5)
    else:
        raise Exception('Database unreachable')

    with app.app_context():
        upgrade()

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
        },
        'disable_existing_loggers': False,
    })

    ma.init_app(app)
    oauth.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    push.init_app(app)

    for blueprint in all_blueprints:
        import_module(blueprint.import_name)
        app.register_blueprint(blueprint)

    # Needed when running behind Nginx under Docker for authorization
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
    return app


def bootstrap_debug():
    '''Create a development-configured application and push its context.
       Helpful for trying queries and DB operations in the REPL.

       Launch IPython and run the following lines:
       ```python
       from innopoints.app import bootstrap_debug
       bootstrap_debug()
       from innopoints.models import *
       from innopoints.extensions import db
       ```

       You'll now have a functioning `db.session` and all models in the namespace.
    '''
    app = create_app('config/dev.py')
    app.app_context().push()
