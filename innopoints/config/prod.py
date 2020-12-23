"""Application configuration for production."""

import os
from base64 import b64decode
from datetime import timedelta

from innopoints.config.common import *


SECRET_KEY = b64decode(os.environ['SECRET_KEY'])

INNOPOLIS_SSO_CLIENT_ID = os.environ['INNOPOLIS_SSO_CLIENT_ID']
INNOPOLIS_SSO_CLIENT_SECRET = os.environ['INNOPOLIS_SSO_CLIENT_SECRET']

SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_DURATION = timedelta(days=60)
PERMANENT_SESSION_LIFETIME = int(REMEMBER_COOKIE_DURATION.total_seconds())

FRONTEND_BASE = 'https://ipts.innopolis.university'

# Until the SSO is properly set up with admin group
admins = [
    'a.blakunovs@innopolis.ru',
    'innopoints@innopolis.university',
]
