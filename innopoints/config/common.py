"""The base application configuration."""

import os


SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

MAIL_SERVER = 'mail.innopolis.ru'
MAIL_PORT = 587
MAIL_USERNAME = 'innopoints@innopolis.university'
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
MAIL_DEFAULT_SENDER = MAIL_USERNAME
MAIL_USE_TLS = True
