"""Views related to the Account model.

Account:
- POST /account/{email}/balance
"""

import logging

from flask import abort, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import Transaction, Account
from innopoints.schemas import AccountSchema

NO_PAYLOAD = ('', 204)
log = logging.getLogger(__name__)


@api.route('/account', defaults={'email': None})
@api.route('/account/<email>')
@login_required
def get_info(email):
    """Get information about an account.
    If the e-mail is not passed, return information about self."""
    if email is None:
        user = current_user
    else:
        if not current_user.is_admin:
            abort(401)
        user = Account.query.get_or_404(email)

    out_schema = AccountSchema(exclude=('moderated_projects', 'created_projects', 'stock_changes',
                                        'transactions', 'applications', 'reports'))
    return out_schema.jsonify(user)


@api.route('/account/<string:email>/balance', methods=['POST'])
@login_required
def change_balance(email):
    """Change a user's balance."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    if not isinstance(request.json.get('change'), int):
        abort(400, {'message': 'The change in innopoints must be specified as an integer.'})

    user = Account.query.get_or_404(email)
    if request.json['change'] != 0:
        new_transaction = Transaction(account=user,
                                      change=request.json['change'])
        db.session.add(new_transaction)
        try:
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            log.exception(err)
            abort(400, {'message': 'Data integrity violated.'})

    return jsonify(balance=user.balance)
