"""The run script.

May be executed directly to start a development server
or fed to servers like gunicorn using `run:app`."""

import os

from innopoints.app import create_app


if __name__ == '__main__':
    app = create_app('config/dev.py')
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 7507), debug=True)
else:
    if os.environ.get('FLASK_ENV') == 'development':
        config = 'config/dev.py'
    else:
        config = 'config/prod.py'
    app = create_app(config)
