release: FLASK_APP=run.py pipenv run flask db upgrade
web: gunicorn run:app --debug
