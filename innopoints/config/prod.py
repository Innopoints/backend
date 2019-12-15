"""Application configuration for production"""

import os
from innopoints.config.common import *

INNOPOLIS_SSO_CLIENT_ID = os.environ['INNOPOLIS_SSO_CLIENT_ID']
INNOPOLIS_SSO_CLIENT_SECRET = os.environ['INNOPOLIS_SSO_CLIENT_SECRET']

def is_admin(userinfo):
    """Determine if the user is an administrator by a dictionary of claims"""
    return False

IS_ADMIN = is_admin
