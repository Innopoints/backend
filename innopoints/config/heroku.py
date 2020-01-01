"""Application configuration for Heroku."""

import re
import os
from innopoints.config.common import *


INNOPOLIS_SSO_CLIENT_ID = os.getenv('INNOPOLIS_SSO_CLIENT_ID')
INNOPOLIS_SSO_CLIENT_SECRET = os.getenv('INNOPOLIS_SSO_CLIENT_SECRET')

JSON_SORT_KEYS = False


CORS_ORIGINS = ['https://innopoints-frontend.herokuapp.com',
                re.compile(r'https?://(?:localhost|0.0.0.0):\d{4}')]

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None
REMEMBER_COOKIE_SECURE = True

FRONTEND_BASE = 'https://innopoints-frontend.herokuapp.com'

IS_ADMIN = lambda userinfo: True
