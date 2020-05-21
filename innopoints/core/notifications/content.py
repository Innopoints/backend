"""Functionality for assembling notification content."""

from dataclasses import dataclass
from urllib.parse import urljoin

from flask import current_app

from innopoints.models import NotificationType, StockChangeStatus, ApplicationStatus
from innopoints.schemas import PayloadSchema


@dataclass
class Link:
    """The representation of a link in notification bodies."""
    title: str
    href: str

    def __str__(self):
        """Return the <a> tag for the link."""
        return '<a href="{}">{}</a>'.format(urljoin(current_app.config["FRONTEND_BASE"], self.href),
                                            self.title)


# pylint: disable=invalid-name
def s(amount):
    """Return the correct pluralization of the amount of items."""
    return 's' if amount != 1 else ''


# pylint: disable=too-many-branches
def get_content(type: NotificationType, payload: dict):
    """Given notification type and payload, returns the data for the notification."""
    payload = payload and PayloadSchema().fill_data(payload.copy())

    title: str = None
    link: str = None
    image_src: str = None
    body: list = None

    if type == NotificationType.purchase_status_changed:
        title = 'Purchase status changed'
        link = f"/products/{payload['product'].id}"
        if payload['variety'].images:
            image_src = payload['variety'].images[0]

        body = ['Your ', str(payload['product']), ' purchase ']

        if payload['stock_change'].status == StockChangeStatus.ready_for_pickup.name:
            body.append('is ready to be picked up at 319 Office.')
        elif payload['stock_change'].status == StockChangeStatus.rejected.name:
            body.append('was rejected.')
        elif payload['stock_change'].status == StockChangeStatus.carried_out.name:
            body.append('was delivered.')
        else:
            body.append('is being processed again.')
    elif type == NotificationType.new_arrivals:
        title = 'New arrivals'
        link = '/store'
        body = ['New products have arrived at the InnoStore.']
    elif type == NotificationType.application_status_changed:
        title = 'Application status changed'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = ['Your volunteering application for ',
                Link(title=payload['activity'].name,
                     href=f"/projects/{payload['project'].id}"),
                ' was ']
        if payload['application'].status == ApplicationStatus.approved:
            body.append('approved.')
        elif payload['application'].status == ApplicationStatus.rejected:
            body.append('rejected.')
        else:
            body.append('moved back to pending.')
    elif type == NotificationType.claim_innopoints:
        _reward = payload['application'].actual_hours * payload['activity'].reward_rate
        title = 'Claim your reward!' if _reward != 0 else 'Leave feedback'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = ['Leave feedback on your volunteering work']
        if _reward != 0:
            body.append(f' to claim {_reward} innopoint{s(_reward)}.')
        else:
            body.append('.')
    elif type == NotificationType.project_review_status_changed:
        title = 'An administrator has reviewed your project'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = [f"The project {payload['project'].name} was "
                f"{payload['project'].review_status} by the administrator."]
    elif type == NotificationType.added_as_moderator:
        title = 'Moderator rights granted'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = [f'You have been promoted to moderate ',
                Link(title=payload['project'].name,
                     href=f"/projects/{payload['project'].id}"),
                '.']
    elif type == NotificationType.all_feedback_in:
        title = 'All feedback collected'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = [f'All volunteers of ',
                Link(title=payload['project'].name,
                     href=f"/projects/{payload['project'].id}"),
                ' have submitted feedback.']
    elif type == NotificationType.out_of_stock:
        title = 'Out of stock'
        link = f"/products/{payload['product'].id}"
        if payload['variety'].images:
            image_src = payload['variety'].images[0]
        body = ['The ',
                Link(title=str(payload['product']),
                     href=f"/products/{payload['product'].id}"),
                ' was sold out.']
    elif type == NotificationType.new_purchase:
        title = 'New purchase'
        link = '/dashboard'
        if payload['variety'].images:
            image_src = payload['variety'].images[0]
        body = [Link(title=payload['account'].full_name,
                     href='/profile?user=' + payload['account'].email),
                ' has purchased the ',
                Link(title=str(payload['product']),
                     href=f"/products/{payload['product'].id}"),
                '.']
    elif type == NotificationType.project_review_requested:
        title = 'Project review requested'
        link = f"/projects/{payload['project'].id}"
        image_src = f"/file/{payload['project'].image_id}"
        body = ['The project ',
                Link(title=payload['project'].name,
                     href=f"/projects/{payload['project'].id}"),
                ' is ready for review.']
    elif type == NotificationType.service:
        title = "Administrator's message"
        body = payload['message']
    elif type == NotificationType.manual_transaction:
        title = 'Your balance has changed'
        body = ['The administrator ']
        if payload['transaction'].change > 0:
            body.append(f"granted {payload['transaction'].change} innopoints to you.")
        else:
            body.append(f"deducted {-payload['transaction'].change} innopoints from you.")
    else:
        title = "Don't mind me"
        body = ['Just a message from heaven wishing you a great day!']

    return {'title': title,
            'body': body,
            'link': link,
            'image': image_src,
            'type': type.value}
