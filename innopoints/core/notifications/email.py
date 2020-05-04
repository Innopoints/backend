'''Email-generating module.'''
from flask import current_app
from flask_mail import Message

from innopoints.models import NotificationType, StockChangeStatus, ApplicationStatus
from innopoints.schemas import PayloadSchema


def convert_links(fragment):
    '''Map two-element tuples to links.'''
    if isinstance(fragment, str):
        return fragment
    return f'<a href="{current_app.config["FRONTEND_BASE"]}{fragment[1]}">{fragment[0]}</a>'


# pylint: disable=too-many-branches
def get_email_message(notification_type, payload, recipient_email):
    '''Convert the payload to a email Message object based on the notification type.'''
    header = None
    body = None
    payload = payload and PayloadSchema().fill_data(payload.copy())

    if notification_type == NotificationType.purchase_status_changed:
        header = 'Purchase status changed'
        body = ['Your ']
        if payload['product'].type is None:
            body.append((payload['product'].name, f"/products/{payload['product'].id}"))
        else:
            body.append((f"'{payload['product'].name}' {payload['product'].type}",
                         f"/products/{payload['product'].id}"))
        body.append(' purchase ')
        if payload['stock_change'].status == StockChangeStatus.ready_for_pickup:
            body.append('is ready to be picked up at 319 Office.')
        elif payload['stock_change'].status == StockChangeStatus.rejected:
            body.append('was rejected.')
        elif payload['stock_change'].status == StockChangeStatus.carried_out:
            body.append('was delivered.')
        else:
            body.append('is being processed again.')
    elif notification_type == NotificationType.new_arrivals:
        header = 'New arrivals'
        body = ['New products have arrived at ', ('the InnoStore', '/store')]
    elif notification_type == NotificationType.application_status_changed:
        header = 'Application status changed'
        body = ['Your volunteering application for ',
                (payload['activity'].name, f"/projects/{payload['project'].id}"),
                ' was ']
        if payload['application'].status == ApplicationStatus.approved:
            body.append('approved')
        elif payload['application'].status == ApplicationStatus.rejected:
            body.append('rejected')
        else:
            body.append('moved back to pending')
    elif notification_type == NotificationType.claim_innopoints:
        header = 'Leave feedback'
        body = ['Leave feedback on ',
                ('your volunteering work', f"/projects/{payload['project'].id}")]
        if payload['application'].actual_hours != 0:
            header = 'Claim your reward!'
            body += [
                ' to claim ',
                str(payload['application'].actual_hours * payload['activity'].reward_rate),
                ' innopoints',
            ]
    elif notification_type == NotificationType.project_review_status_changed:
        header = 'An administrator has reviewed your project'
        body = ['The project ',
                (payload['project'].name, f"/projects/{payload['project'].id}"),
                ' was ',
                payload['project'].review_status,
                ' by the administrator']
    elif notification_type == NotificationType.added_as_moderator:
        header = 'Moderator rights'
        body = ['You have been promoted to moderate ',
                (payload['project'].name, f"/projects/{payload['project'].id}")]
    elif notification_type == NotificationType.all_feedback_in:
        header = 'All feedback collected'
        body = ['All volunteers of ',
                (payload['project'].name, f"/projects/{payload['project'].id}"),
                ' have submitted feedback']
    elif notification_type == NotificationType.out_of_stock:
        header = 'Out of stock'
        body = ['The ']
        if payload['product'].type is None:
            body.append((payload['product'].name, f"/products/{payload['product'].id}"))
        else:
            body.append((f"'{payload['product'].name}' {payload['product'].type}",
                         f"/products/{payload['product'].id}"))
        body.append(' was sold out')
    elif notification_type == NotificationType.new_purchase:
        header = 'New purchase'
        body = [(payload['account'].full_name, '/profile?user=' + payload['account'].email),
                ' has purchased the ']
        if payload['product'].type is None:
            body.append((payload['product'].name, f"/products/{payload['product'].id}"))
        else:
            body.append((f"'{payload['product'].name}' {payload['product'].type}",
                         f"/products/{payload['product'].id}"))
    elif notification_type == NotificationType.project_review_requested:
        header = 'Project review requested'
        body = ['The project ',
                (payload['project'].name, f"/projects/{payload['project'].id}"),
                ' is ready for review']
    elif notification_type == NotificationType.service:
        header = 'Administrator\'s message'
        body = payload['message']
    elif notification_type == NotificationType.manual_transaction:
        header = 'Your balance has changed'
        body = ['The administrator ']
        if payload['transaction'].change > 0:
            body.append(f"granted {payload['transaction'].change} innopoints to you")
        else:
            body.append(f"deducted ${-payload['transaction'].change} innopoints from you")
    else:
        header = 'Don\'t mind me'
        body = ['Just a message from heaven wishing you a great day']

    body = ''.join(map(convert_links, body)) + '.'

    with open('templates/email.html') as email_template:
        return Message(header,
                       recipients=[recipient_email],
                       html=email_template.read().format(header=header, body=body))
