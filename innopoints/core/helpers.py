"""Miscellaneous helper functions."""

import hmac
import json

from flask import abort as flask_abort, Response, session, request


MODIFYING_METHODS = ('POST', 'PATCH', 'DELETE')


def abort(http_code: int, message=None):
    """Wraps the default Flask's abort function to return a plain JSON response."""
    if message is not None:
        flask_abort(Response(json.dumps(message), status=http_code, mimetype='application/json'))
    else:
        flask_abort(Response(status=http_code))


def csrf_protect():
    """Validates the CSRF token for modifying requests (POST, PATCH, DELETE)."""
    if request.method not in MODIFYING_METHODS:
        return

    if not hmac.compare_digest(request.headers.get('X-CSRF-Token'), session['csrf_token']):
        abort(403)
