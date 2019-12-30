"""Application configuration for Heroku."""

import os
from innopoints.config.common import *


INNOPOLIS_SSO_CLIENT_ID = os.getenv('INNOPOLIS_SSO_CLIENT_ID')
INNOPOLIS_SSO_CLIENT_SECRET = os.getenv('INNOPOLIS_SSO_CLIENT_SECRET')

JSON_SORT_KEYS = False

CORS_ORIGINS = 'https://innopoints-frontend.herokuapp.com'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None
REMEMBER_COOKIE_SECURE = True

IS_ADMIN = lambda userinfo: True
