from flask.testing import FlaskClient


class JsonCapableTestClient(FlaskClient):
    '''Extend the built-in testing client with functionality specific to JSON endpoints.'''

    def json(self, *args, **kwargs):
        '''Ensure that the response code is OK and the content type is set correctly.
           Return the parsed JSON body of the response.'''
        response = self.get(*args, **kwargs)
        assert response.status_code == 200
        assert response.is_json
        return response.get_json()
