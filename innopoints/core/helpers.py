"""Miscellaneous helper functions."""

import hmac
import json
from functools import wraps

from flask import abort as flask_abort, Response, session, request, current_app
from flask_login import login_required, current_user
from werkzeug.routing import NotFound


BODY_METHODS = ('POST', 'PATCH')
MODIFYING_METHODS = ('POST', 'PATCH', 'DELETE')


def abort(http_code: int, message=None):
    """Wraps the default Flask's abort function to return a plain JSON response."""
    if message is not None:
        flask_abort(Response(json.dumps(message), status=http_code, mimetype='application/json'))
    else:
        flask_abort(Response(status=http_code))


def csrf_protect():
    """Validates the CSRF token for modifying requests (POST, PATCH, DELETE)."""
    if current_app.config['ENV'] == 'development':  # skip the check in development
        return

    if request.method not in MODIFYING_METHODS:
        return

    if not hmac.compare_digest(request.headers.get('X-CSRF-Token', ''),
                               session.get('csrf_token', '')):
        abort(403, {'message': 'CSRF token invalid.'})


json_exempt_views = []
def allow_no_json(view):
    """Explicitly exempt the request from the JSON Content-Type check.
       **Important**: this must be the topmost decorator."""
    json_exempt_views.append(view)
    return view


def require_json():
    """Ensure JSON Content-Type for requests with a body (POST, PATCH)."""
    if request.method not in BODY_METHODS:
        return

    try:
        view = current_app.view_functions.get(request.endpoint)
        if view not in json_exempt_views and not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})
    except NotFound:
        pass


def admin_required(view):
    """Ensure only admins can access the decorated view."""
    @wraps(view)
    def permission_checked(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return login_required(permission_checked)
