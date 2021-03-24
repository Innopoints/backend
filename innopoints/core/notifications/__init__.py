"""Helper module for sending notifications, depending on the user preference"""

import logging
import threading
from typing import Sequence

from flask import copy_current_request_context
from flask_mail import Message
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db, mail
from innopoints.models import Notification, NotificationType, Account, type_to_group
from .content import get_content
from .push import push

log = logging.getLogger(__name__)


def notify(recipient_email: str, notification_type: NotificationType, payload=None):
    """Sends a notification to the specified user."""
    notification_group = type_to_group[notification_type]
    channel = db.session.query(
        # pylint: disable=unsubscriptable-object
        Account.notification_settings[notification_group]
    ).filter(Account.email == recipient_email).scalar()

    if channel == 'email':
        message_content = get_content(notification_type, payload)
        body = ''.join(map(str, message_content['body']))

        with open('templates/email.html') as email_template:
            message = Message(message_content['title'],
                              recipients=[recipient_email],
                              html=email_template.read().format(header=message_content['title'],
                                                                body=body))

        @copy_current_request_context
        def send_mail_async(message):
            mail.send(message)

        mail_thread = threading.Thread(name='mail_sender', target=send_mail_async, args=(message,))
        mail_thread.start()
        log.info(f'Sent an email to {recipient_email}')
    elif channel == 'push':
        push(recipient_email, notification_type, payload)

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


def notify_all(recipients: Sequence[Account], notification_type: str, payload=None):
    """Sends the same notification to each of the emails in the given list."""
    for recipient in recipients:
        notify(recipient.email, notification_type, payload)


def remove_notifications(payload: dict):
    """Deletes notifications whose payload has any of the entries in the given payload."""
    deleted = 0
    for key, value in payload.items():
        query = Notification.query.filter(Notification.payload.isnot(None))
        query = query.filter(
            # pylint: disable=unsubscriptable-object
            Notification.payload[key].astext == str(value)
        )
        deleted += query.delete(synchronize_session=False)
    try:
        db.session.commit()
        log.debug(f'Deleted {deleted} notification(s) matching "{payload}"')
    except IntegrityError as exc:
        db.session.rollback()
        log.exception(exc)
    return deleted
