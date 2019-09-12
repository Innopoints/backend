# Innopoints Backend

## Prerequisites

You need to have [Pipenv](https://github.com/pypa/pipenv) installed to set up the project environment.

**Arch Linux**:
```bash
$ pacman -S python-pipenv
```

## Install the dependencies

```bash
$ pipenv install --dev
```

## Set up the database
Ensure that PostgreSQL is installed and functioning. Create a database and substitute `{database_name}` in the following commands.

```bash
$ export DATABASE_URL='postgresql://localhost/{database_name}'
$ export INNOPOINTS_DATABASE_URI='postgresql://localhost/{database_name}'
# for fish:
#  set -x DATABASE_URL 'postgresql://localhost/{database_name}'
#  set -x INNOPOINTS_DATABASE_URI 'postgresql://localhost/{database_name}'
$ cd innopoints
$ pipenv run flask db init
$ pipenv run flask db migrate
$ pipenv run flask db upgrade
$ cd ..
```

## Run the server

```bash
$ pipenv run python run.py
```
