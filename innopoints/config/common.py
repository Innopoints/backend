"""The base application configuration."""

import os


SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_ENGINE_OPTIONS = {'future': True}
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
REMEMBER_COOKIE_SAMESITE = 'Lax'

MAIL_SERVER = 'mail.innopolis.ru'
MAIL_PORT = 587
MAIL_USERNAME = 'innopoints@innopolis.university'
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
MAIL_DEFAULT_SENDER = MAIL_USERNAME
MAIL_USE_TLS = True
WEBPUSH_VAPID_PRIVATE_KEY = os.environ.get('WEBPUSH_VAPID_PRIVATE_KEY')
WEBPUSH_SENDER_INFO = os.environ.get('WEBPUSH_SENDER_INFO')
