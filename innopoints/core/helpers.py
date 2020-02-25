"""Miscellaneous helper functions."""

import json

from flask import abort as flask_abort, Response


def abort(http_code: int, message=None):
    """Wraps the default Flask's abort function to return a plain JSON response."""
    if message is not None:
        flask_abort(
            Response(json.dumps(message), status=http_code, mimetype='application/json')
        )
    else:
        flask_abort(Response(status=http_code))
