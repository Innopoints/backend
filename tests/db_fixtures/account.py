'''Fixtures defined for all tests.'''

import secrets

from flask import session
from flask_login import login_user, logout_user
import pytest

from innopoints.extensions import db
from innopoints.models import Account


@pytest.fixture
def students(faker):
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
def admins(faker):
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
def logged_in_student(app, students, faker):
    '''Log in and return one of the students.'''
    the_user = faker.random_element(students)

    login_user(the_user, remember=True)
    session['csrf_token'] = secrets.token_urlsafe()
    session.permanent = True

    yield (the_user, session['csrf_token'])

    logout_user()


@pytest.fixture()
def logged_in_admin(app, admins, faker):
    '''Log in and return one of the admins.'''
    the_user = faker.random_element(admins)

    login_user(the_user, remember=True)
    session['csrf_token'] = secrets.token_urlsafe()
    session.permanent = True

    yield (the_user, session['csrf_token'])

    logout_user()
