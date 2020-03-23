"""Helper module for sending notifications, depending on the user preference"""

import logging
from typing import List

from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.models import Notification, NotificationType, Account, type_to_group

log = logging.getLogger(__name__)


def notify(recipient_email: str, notification_type: NotificationType, payload=None):
    """Sends a notification to the specified user."""
    notification_group = type_to_group[notification_type]
    channel = db.session.query(
        # pylint: disable=unsubscriptable-object
        Account.notification_settings[notification_group]
    ).filter_by(email=recipient_email).scalar()

    if channel == 'email':
        # TODO: send Email
        pass
    elif channel == 'push':
        # TODO: send Push
        pass

    notification = Notification(
        recipient_email=recipient_email,
        type=notification_type,
        payload=payload,
    )

    try:
        db.session.add(notification)
        db.session.commit()
        log.info(f'Sent a notification to {recipient_email}')
        return notification
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
        return None


def notify_all(recipients: List[Account], notification_type: str, payload=None):
    """Sends the same notification to each of the emails in the given list."""
    for recipient in recipients:
        notify(recipient.email, notification_type, payload)


def remove_notifications(payload: dict):
    """Deletes notifications whose payload has any of the entries in the given payload."""
    deleted = 0
    for k, v in payload.items():
        query = Notification.query.filter(Notification.payload.isnot(None))
        query = query.filter(Notification.payload[k].astext == str(v))
        deleted += query.delete(synchronize_session=False)
    try:
        db.session.commit()
        log.debug(f'Deleted {deleted} notification(s) matching "{payload}"')
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
    return deleted
