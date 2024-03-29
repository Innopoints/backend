"""Flask extensions are instantiated here.

To avoid circular imports with views and create_app(), extensions are instantiated here.
They will be initialized (calling init_app()) in app.py.
"""

import os

from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_pywebpush import WebPush


db = SQLAlchemy(session_options={'future': True})

ma = Marshmallow()

oauth = OAuth()
oauth.register(
    'innopolis_sso',
    server_metadata_url=f'{os.getenv("INNOPOLIS_SSO_BASE")}/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid'},
)

login_manager = LoginManager()
login_manager.session_protection = 'basic'

mail = Mail()

push = WebPush()
