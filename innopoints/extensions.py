"""Flask extensions are instantiated here.

To avoid circular imports with views and create_app(), extensions are instantiated here.
They will be initialized (calling init_app()) in app.py.
"""

import json
import os

from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from pywebpush import webpush, WebPushException


class WebPush:
    def __init__(self, app=None):
        self.public_key = None
        self.private_key = None
        self.sender_info = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.public_key = app.config.get('WEBPUSH_VAPID_PUBLIC_KEY')
        self.private_key = app.config.get('WEBPUSH_VAPID_PRIVATE_KEY')
        self.sender_info = app.config.get('WEBPUSH_SENDER_INFO')

    def send(self, subscription, notification):
        webpush(subscription,
                json.dumps(notification),
                vapid_private_key=self.private_key,
                vapid_claims={"sub": self.sender_info})


db = SQLAlchemy()

ma = Marshmallow()

oauth = OAuth()
oauth.register(
    'innopolis_sso',
    server_metadata_url=f'{os.environ["INNOPOLIS_SSO_BASE"]}/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid'},
)

login_manager = LoginManager()
login_manager.session_protection = 'basic'

mail = Mail()

push = WebPush()
