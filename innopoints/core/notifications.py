"""Helper module for sending notifications, depending on the user preference"""

import logging
from typing import List

from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.models import Notification, Account

log = logging.getLogger(__name__)


def notify(recipient_email: str, notification_type: str, payload=None):
    """Sends a notification to the specified user."""
    # TODO: check preferences
    # TODO: send Email
    # TODO: send Push
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
