"""Run script"""

import os

from innopoints.app import create_app


if __name__ == '__main__':
    app = create_app('config/dev.py')
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 7507), debug=True)
else:
    print(os.environ.get('FLASK_DEV'))
    if os.environ.get('FLASK_DEV') is not None:
        config = 'config/dev.py'
    else:
        config = 'config/prod.py'
    app = create_app(config)
