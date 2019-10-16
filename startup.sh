pipenv install --dev
cd innopoints
pipenv run flask db init
pipenv run flask db migrate
pipenv run flask db upgrade
cd ..
gunicorn run:app
