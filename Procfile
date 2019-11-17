release: mkdir -p migrations/versions && FLASK_APP=run.py pipenv run flask db migrate && FLASK_APP=run.py pipenv run flask db upgrade
web: gunicorn run:app
