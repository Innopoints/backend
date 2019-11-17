"""Application configuration for development"""

import os

SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False

INNOPOLIS_SSO_CLIENT_ID = os.environ.get('INNOPOLIS_SSO_CLIENT_ID')
INNOPOLIS_SSO_CLIENT_SECRET = os.environ.get('INNOPOLIS_SSO_CLIENT_SECRET')

JSON_SORT_KEYS = False

def is_admin(userinfo):
    """Determine if the user is an administrator by a dictionary of claims"""
    return True

IS_ADMIN = is_admin
