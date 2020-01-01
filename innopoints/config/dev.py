"""Application configuration for local development."""

import re
import os
from innopoints.config.common import *


INNOPOLIS_SSO_CLIENT_ID = os.getenv('INNOPOLIS_SSO_CLIENT_ID')
INNOPOLIS_SSO_CLIENT_SECRET = os.getenv('INNOPOLIS_SSO_CLIENT_SECRET')

JSON_SORT_KEYS = False

CORS_ORIGINS = [re.compile(r'https?://(?:localhost|0.0.0.0):\d{4}')]

IS_ADMIN = lambda userinfo: True
