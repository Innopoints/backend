"""Application configuration for development"""

import os

SQLALCHEMY_DATABASE_URI = os.environ['INNOPOINTS_DATABASE_URI']
SQLALCHEMY_TRACK_MODIFICATIONS = False
