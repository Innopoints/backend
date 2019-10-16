"""Run script"""

import os

from innopoints.app import create_app


if __name__ == '__main__':
    app = create_app('config/prod.py')  # pylint: disable=invalid-name
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 7507))
else:
    app = create_app()  # pylint: disable=invalid-name
