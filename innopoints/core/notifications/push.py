"""Helper module for sending notifications, depending on the user preference"""

import logging
from json import dumps

from flask import current_app
from pywebpush import webpush, WebPushException

from innopoints.models import NotificationType, Account

log = logging.getLogger(__name__)


def get_content(notification_type: str, payload):
    '''Given notification type and payload, returns the data for the notification'''
    # default values
    title = 'Innopoints notification'
    body = 'Something happened.'
    link = '/'
    if notification_type == NotificationType.purchase_status_changed:
        title = 'Purchase status changed'
        if payload['product'].type is None:
            purchase = payload['product'].name
        else:
            purchase = f"'{payload['product'].name}' {payload['product'].type}"
        if payload['stock_change'].status == StockChangeStatus.ready_for_pickup:
            status_update = 'is ready to be picked up at 319 Office.'
        elif payload['stock_change'].status == StockChangeStatus.rejected:
            status_update = 'was rejected.'
        elif payload['stock_change'].status == StockChangeStatus.carried_out:
            status_update = 'was delivered.'
        else:
            status_update = 'is being processed again.'
        body = f'Your {purchase} purchase {status_update}'
        link = f'/products/{payload["product"].id}'
    elif notification_type == NotificationType.new_arrivals:
        title = 'New arrivals'
        body = 'New products have arrived at the InnoStore'
        link = '/store'
    elif notification_type == NotificationType.application_status_changed:
        title = 'Application status changed'
        if payload['application'].status == ApplicationStatus.approved:
            status = 'approved'
        elif payload['application'].status == ApplicationStatus.rejected:
            status = 'rejected'
        else:
            status = 'moved back to pending'
        body = f'Your volunteering application for {payload["activity"].name} was {status}'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.claim_innopoints:
        title = 'Claim your reward!'
        reward = payload['application'].actual_hours * payload['activity'].reward_rate
        body = f'Leave feedback on your volunteering work to claim {reward} innopoints'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.project_review_status_changed:
        title = 'An administrator has reviewed your project'
        body = f'The project {payload["project"].name} was {payload["project"].review_status} by the administrator'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.added_as_moderator:
        title = 'Moderator rights'
        body = f'You have been promoted to moderate {payload["project"].name}'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.all_feedback_in:
        title = 'All feedback collected'
        body = f'All volunteers of {payload["project"].name} have submitted feedback'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.out_of_stock:
        title = 'Out of stock'
        if payload['product'].type is None:
            product_name = payload['product'].name
        else:
            product_name = f"'{payload['product'].name}' {payload['product'].type}"
        body = f'The {product_name} was sold out'
        link = f"/products/{payload['product'].id}"
    elif notification_type == NotificationType.new_purchase:
        title = 'New purchase'
        if payload['product'].type is None:
            product_name = payload['product'].name
        else:
            product_name = f"'{payload['product'].name}' {payload['product'].type}"
        body = f"{payload['account'].full_name} has purchased the {product_name}"
        link = '/dashboard'
    elif notification_type == NotificationType.project_review_requested:
        title = 'Project review requested'
        body = f'The project {payload["project"].name} is ready for review'
        link = f"/projects/{payload['project'].id}"
    elif notification_type == NotificationType.service:
        title = 'Administrator\'s message'
        body = payload['message']
    elif notification_type == NotificationType.manual_transaction:
        title = 'Your balance has changed'
        body = 'The administrator '
        if payload['transaction'].change > 0:
            body += f"granted {payload['transaction'].change} innopoints to you"
        else:
            body += f"deducted ${-payload['transaction'].change} innopoints from you"
    return {
        'title': title,
        'body': body,
        'link': link,
    }


def push(recipient_email: str, notification_type: NotificationType, payload=None):
    '''Sends a notification to the specified user.'''
    subscriptions = Account.query.get(recipient_email).notification_settings['subscriptions']
    try:
        data = get_content(notification_type, payload)
    except KeyError:
        data = str(payload)
    try:
        for subscription_info in subscriptions:
            webpush(subscription_info,
                    dumps(data),
                    vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
                    vapid_claims={"sub": "mailto:innopoints@innopolis.university"}
            )
    except WebPushException as ex:
        log.exception(ex)

# TODO: move subscribe method from views to here
# TODO: create unsubscribe method to remove all (or some) push subscriptions
