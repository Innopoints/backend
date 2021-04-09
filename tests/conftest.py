'''Fixtures defined for all tests.'''

import os
from base64 import b64encode
from typing import Generator

import pytest
pytest.register_assert_rewrite('tests.json_capable_test_client')
from flask import Flask

from innopoints.app import create_app
from tests.json_capable_test_client import JsonCapableTestClient

configs = [
    ('config/dev.py', ' dev'),
    ('config/prod.py', 'prod'),
]
params, ids = zip(*configs)


@pytest.fixture(scope='session', params=params, ids=ids)
def app(request: pytest.FixtureRequest) -> Generator[Flask, None, None]:
    '''Create a Flask app with all possible configurations.'''
    secret_key = b64encode(b'swiper-no-swiping').decode()
    old_value = os.getenv('SECRET_KEY')
    os.environ['SECRET_KEY'] = secret_key

    app = create_app(config=request.param)
    app.config['TESTING'] = True
    with app.app_context():
        yield app

    if old_value is not None:
        os.environ['SECRET_KEY'] = old_value


@pytest.fixture
def client(app: Flask) -> Generator[JsonCapableTestClient, None, None]:
    '''Spin up a test client for the current Flask app.'''
    app.test_client_class = JsonCapableTestClient
    with app.test_client() as client:
        yield client
