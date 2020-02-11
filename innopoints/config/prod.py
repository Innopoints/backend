"""Application configuration for production."""

import os
from innopoints.config.common import *


SECRET_KEY = os.environ['SECRET_KEY']

INNOPOLIS_SSO_CLIENT_ID = os.environ['INNOPOLIS_SSO_CLIENT_ID']
INNOPOLIS_SSO_CLIENT_SECRET = os.environ['INNOPOLIS_SSO_CLIENT_SECRET']

CORS_ORIGINS = []

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = None
REMEMBER_COOKIE_SECURE = True

FRONTEND_BASE = 'https://ipts.innopolis.university'


def is_admin(userinfo):  # pylint: disable=unused-argument
    """Determine if the user is an administrator by a dictionary of claims."""
    return False

IS_ADMIN = is_admin
