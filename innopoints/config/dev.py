"""Application configuration for local development."""

import os
from innopoints.config.common import *


SECRET_KEY = b'\xdb4\xab_\xb0\xbf\xc2L\x86H<\xc8^\xc0\x95\xb7'

INNOPOLIS_SSO_CLIENT_ID = os.getenv('INNOPOLIS_SSO_CLIENT_ID')
INNOPOLIS_SSO_CLIENT_SECRET = os.getenv('INNOPOLIS_SSO_CLIENT_SECRET')

JSON_SORT_KEYS = False

FRONTEND_BASE = 'http://0.0.0.0:3000'

IS_ADMIN = lambda userinfo: True
