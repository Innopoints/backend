# Innopoints

This is the backend for the Innopoints portal of Innopolis University.

Built using:
 - [Flask](https://flask.palletsprojects.com/en/1.1.x/)
 - [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)
 - [SQLAlchemy](https://www.sqlalchemy.org/)
 - [PostgreSQL](https://www.postgresql.org/)
 - [Marshmallow](https://marshmallow.readthedocs.io/en/stable/)

## Running locally

This project was built for Python 3.8.

You need to have [Pipenv](https://github.com/pypa/pipenv) installed to set up the project environment.  
Ensure that the PostgreSQL server is up and running. Create a database and substitute its name in place of `{database_name}` in the following commands.  

Create a `.env` file in the project root and supply values for the necessary environment variables:

```bash
DATABASE_URL=postgresql://localhost/{database_name}
MAIL_PASSWORD={service-account-mail-password}
FLASK_APP=run.py

# If you will use the Innopolis SSO
INNOPOLIS_SSO_BASE=https://sso.university.innopolis.ru/adfs
INNOPOLIS_SSO_CLIENT_ID={sso-client-id}
INNOPOLIS_SSO_CLIENT_SECRET={sso-client-secret}

# If you will use push notifications
WEBPUSH_VAPID_PRIVATE_KEY={vapid-private-key}
WEBPUSH_SENDER_INFO={push-sender-info}

# If you want to run the server with the development configuration
FLASK_ENV=development
```

To install the dependencies and run the development server, run the following commands:

```bash
pipenv install
pipenv run start
```

## Project structure

The main components of the project are:
 - SQLAlchemy models ([`innopoints/models`](./innopoints/models))
 - Marshmallow schemas ([`innopoints/schemas`](./innopoints/schemas))
 - Flask views ([`innopoints/views`](./innopoints/views))

Those three folders contain files under the same names to make it easy to follow.

Models define the database entities.

Schemas define the way the models are serialized into JSON to be served by the API.

Views define the API endpoints themselves.

Flask [extensions](./innopoints/extensions.py) and [blueprints](./innopoints/blueprints.py) have been moved to separate files to prevent circular imports.

## Modifying the database entities

The database migration history is powered by Flask-Migrate. All the migrations are stored in the `migrations/versions` folder. If you make any changes to the models, make sure to persist your changes to the database with the following commands:

```bash
# To snapshot the changes into a migration
pipenv run new-migration -m "Make some changes"
# To apply the migration to the database
pipenv run apply-migrations
```

**Warning**: Flask-Migrate uses Alembic to analyze the models and autogenerate migrations. There are [some things Alebmic cannot detect](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect). Make sure you compare the migration created by Alembic with your changes and manually change the migration if necessary.

## License
This project is [MIT licensed](./LICENSE).
