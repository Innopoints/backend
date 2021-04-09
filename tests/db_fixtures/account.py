'''Fixtures defined for all tests.'''

import secrets
from typing import Generator, List, Tuple

import flask_login
import pytest
from faker import Faker
from flask import Flask, session as top_level_session

from innopoints.extensions import db
from innopoints.models import Account
from tests.json_capable_test_client import JsonCapableTestClient


def login_user(user: Account, app: Flask, client: JsonCapableTestClient, csrf_token: str):
    '''Log in a particular user for the current instance of the test client.'''

    with app.test_request_context('/login'):
        # Here's the deal:
        #   `login_user()` requires a request context to operate.
        #   Within that request context, it mutates the session
        #   (accessed through the top-level proxy, `from flask import Session`).
        #   The changes that are made to that session will disappear whenever
        #   the request context is popped.
        #
        #   One way to persist these changes is by opening a session transaction,
        #   within which we can arbitrarily modify the session that the test client
        #   has. Those modifications will be written upon exiting the transaction.
        #   Note that the session object that is received in that context manager
        #   is essentially fresh, which is why we need to copy over the changes
        #   made by `login_user()` from the top-level session to the client's one.
        flask_login.login_user(user, fresh=True)
        with client.session_transaction() as session:
            for key in top_level_session:
                if key not in session:
                    session[key] = top_level_session[key]
            session['csrf_token'] = csrf_token
            session.permanent = True


@pytest.fixture
def students(faker: Faker) -> Generator[List[Account], None, None]:
    '''Generate some students.'''
    users = [
        Account(full_name=faker.name(),
                group=faker.numerify('B##-01'),
                email=faker.safe_email(),
                telegram_username=None,
                is_admin=False),
        Account(full_name=faker.name(),
                group=faker.numerify('B##-SE-01'),
                email=faker.safe_email(),
                telegram_username=faker.user_name(),
                is_admin=False),
        Account(full_name=faker.name(),
                group=faker.numerify('M##-SNE-01'),
                email=faker.safe_email(),
                telegram_username=faker.user_name(),
                is_admin=False),
        Account(full_name=faker.name(),
                group=faker.numerify('M##-SNE-01'),
                email=faker.safe_email(),
                telegram_username=faker.user_name(),
                is_admin=False),
    ]
    db.session.add_all(users)
    db.session.commit()

    yield users

    for user in users:
        db.session.delete(user)
    db.session.commit()


@pytest.fixture
def admins(faker: Faker) -> Generator[List[Account], None, None]:
    '''Generate some admins.'''
    users = [
        Account(full_name=faker.name(),
                group='Отдел поддержки и развития студентов',
                email=faker.safe_email(),
                telegram_username=None,
                is_admin=True),
        Account(full_name=faker.name(),
                group='Department of Education',
                email=faker.safe_email(),
                telegram_username=faker.user_name(),
                is_admin=True),
        Account(full_name=faker.name(),
                group=faker.numerify('M##-SNE-01'),
                email=faker.safe_email(),
                telegram_username=faker.user_name(),
                is_admin=True),
    ]
    db.session.add_all(users)
    db.session.commit()

    yield users

    for user in users:
        db.session.delete(user)
    db.session.commit()


@pytest.fixture()
def logged_in_student(
    app: Flask,
    client: JsonCapableTestClient,
    students: List[Account],
    faker: Faker,
) -> Tuple[Account, str]:
    '''Log in and return one of the students.'''
    the_user = faker.random_element(students)
    csrf_token = secrets.token_urlsafe()

    login_user(the_user, app, client, csrf_token)

    return (the_user, csrf_token)


@pytest.fixture()
def logged_in_admin(
    app: Flask,
    client: JsonCapableTestClient,
    admins: List[Account],
    faker: Faker,
) -> Tuple[Account, str]:
    '''Log in and return one of the admins.'''
    the_user = faker.random_element(admins)
    csrf_token = secrets.token_urlsafe()

    login_user(the_user, app, client, csrf_token)

    return (the_user, csrf_token)
