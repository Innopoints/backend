"""Blueprint creation module. Allows specifying the name and the URL prefix.

To register a blueprint, add it to the `all_blueprints` tuple.
"""

from flask import Blueprint

from innopoints.core.helpers import csrf_protect, require_json


def _factory(partial_module_string, url_prefix='/'):
    """Generates blueprint objects for view modules.
    Positional arguments:
    partial_module_string -- string representing a view module without
        the absolute path (e.g. 'home.index' for pypi_portal.views.home.index).
    url_prefix -- URL prefix passed to the blueprint.
    Returns:
    Blueprint instance for a view module.
    """
    name = partial_module_string
    import_name = 'innopoints.views'
    blueprint = Blueprint(name, import_name, url_prefix=url_prefix)

    @blueprint.errorhandler(401)
    def _unauthorized_no_body(_error):
        '''Prevent sending the HTML body with the 401 response.'''
        return '', 401

    @blueprint.errorhandler(403)
    def _forbidden_no_body(_error):
        '''Prevent sending the HTML body with the 403 response.'''
        return '', 403

    return blueprint


api = _factory('api', url_prefix='/api/v1')
api.before_request(csrf_protect)
api.before_request(require_json)
auth = _factory('auth')

all_blueprints = (api, auth)
