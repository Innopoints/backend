"""Run script"""

from innopoints.app import create_app


if __name__ == '__main__':
    app = create_app('config/dev.py')  # pylint: disable=invalid-name
    app.run(host='0.0.0.0', port=7507)
else:
    app = create_app()  # pylint: disable=invalid-name
