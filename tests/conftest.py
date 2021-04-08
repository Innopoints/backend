'''Fixtures defined for all tests.'''

import os
from base64 import b64encode

import pytest

from innopoints.app import create_app

configs = [
    ('config/dev.py', ' dev'),
    ('config/prod.py', 'prod'),
]
params, ids = zip(*configs)


@pytest.fixture(scope='session', params=params, ids=ids)
def app(request):
    '''Create a Flask app with all possible configurations.'''
    secret_key = b64encode(b'swiper-no-swiping').decode()
    old_value = os.getenv('SECRET_KEY')
    os.environ['SECRET_KEY'] = secret_key

    yield create_app(config=request.param)

    if old_value is not None:
        os.environ['SECRET_KEY'] = old_value
