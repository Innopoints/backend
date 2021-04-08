import pytest

pytest_plugins = 'tests.db_fixtures.account'


@pytest.mark.usefixtures('client_class')
class TestGetInfo:
    '''Test the `/account` endpoint (and its alias, `/accounts/:email`)'''

    def test_with_student(self, logged_in_student):
        '''When a regular student is logged in.'''
        response = self.client.get('/api/v1/account')
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data == {}

    def test_with_admin(self, logged_in_admin):
        '''When an administrator is logged in.'''

    def test_without_login(self):
        '''When the requester is not authenticated.'''
