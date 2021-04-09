import pytest
from flask import session
from flask_login import login_user, logout_user

pytest_plugins = 'tests.db_fixtures.account'


class TestGetInfo:
    '''Test the `/account` endpoint (and its alias, `/accounts/:email`)'''

    def test_with_student(self, client, logged_in_student):
        '''When a regular student is logged in.'''
        response = client.get('/api/v1/account')
        assert response.status_code == 200
        user, csrf_token = logged_in_student

        response_data = response.get_json()
        expected_data = {
            'email': user.email,
            'full_name': user.full_name,
            'group': user.group,
            'telegram_username': user.telegram_username,
            'is_admin': user.is_admin,
            'balance': user.balance,
        }
        assert response_data == expected_data

    # def test_with_admin(self, logged_in_admin):
    #     '''When an administrator is logged in.'''
    #
    # def test_without_login(self):
    #     '''When the requester is not authenticated.'''
