# Innopoints Backend

## Prerequisites

You need to have [Pipenv](https://github.com/pypa/pipenv) installed to set up the project environment.

**Arch Linux**:
```bash
$ pacman -S python-pipenv
```

## Install the dependencies

```bash
$ pipenv install
```

## Run the server
Ensure that PostgreSQL is installed and functioning. Create a database and substitute `{database_name}` in the following commands.

```bash
$ export DATABASE_URL='postgresql://localhost/{database_name}'
$ export INNOPOLIS_SSO_BASE='https://sso.university.innopolis.ru/adfs'
$ export INNOPOLIS_SSO_CLIENT_ID='{application-client-id}'
$ export INNOPOLIS_SSO_CLIENT_SECRET='{application-secret}'
$ export FLASK_ENV='debug'  # to use the development config
# for fish:
#  set -x DATABASE_URL 'postgresql://localhost/{database_name}'
#  set -x INNOPOLIS_SSO_BASE 'https://sso.university.innopolis.ru/adfs'

$ pipenv run gunicorn run:app
```
