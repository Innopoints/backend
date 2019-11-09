"""Application configuration for development"""

import json
import os

SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False

INNOPOLIS_SSO_CLIENT_ID = os.environ['INNOPOLIS_SSO_CLIENT_ID']
INNOPOLIS_SSO_CLIENT_SECRET = os.environ['INNOPOLIS_SSO_CLIENT_SECRET']

ADMINS = json.loads(os.environ.get(
    'ADMINS', '["l.chelyadinov@innopolis.university","a.abounegm@innopolis.university"]'))
