"""Helper module for sending notifications, depending on the user preference"""

import logging

from pywebpush import WebPushException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from innopoints.extensions import push as webpush, db
from innopoints.models import NotificationType, Account
from innopoints.schemas import PayloadSchema
from .content import get_content, Link


log = logging.getLogger(__name__)


def remove_links(fragment):
    """Replace Link objects with their titles (no links allowed in push notifications)."""
    if isinstance(fragment, Link):
        return fragment.title
    return fragment



def push(recipient_email: str, notification_type: NotificationType, payload=None):
    '''Sends a notification to the specified user.'''
    subscriptions = Account.query.get(recipient_email).notification_settings.get('subscriptions')
    if subscriptions is None:
        log.error(f'User {recipient_email} is not subscribed to push notifications.')
        return

    try:
        payload = PayloadSchema().dump(payload.copy())
        data = get_content(notification_type, payload)
        data['body'] = ''.join(map(remove_links, data['body']))
    except KeyError:
        data = payload

    for subscription in subscriptions:
        try:
            webpush.send(subscription, data)
        except WebPushException as ex:
            log.exception(ex)


def subscribe(user, subscription_information):
    '''Add the subscription information to the list of the user's push subscriptions.'''
    settings = user.notification_settings
    settings.update({
        'subscriptions': settings.get('subscriptions', []) + [subscription_information]
    })
    flag_modified(user, 'notification_settings')

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
        raise exc


# TODO: create unsubscribe method to remove all (or some) push subscriptions
