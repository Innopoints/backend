"""Views responsible for authentication.

- GET /login
- GET /authorize
- GET /logout
"""

import secrets
from urllib.parse import urljoin

from flask import current_app, url_for, redirect, session, request
from flask_login import login_user, logout_user
from authlib.common.errors import AuthlibBaseError
from authlib.jose.errors import MissingClaimError, InvalidClaimError

from innopoints.blueprints import auth
from innopoints.core.helpers import abort
from innopoints.extensions import oauth, db
from innopoints.models import Account

NO_PAYLOAD = ('', 204)


@auth.route('/login')
def login():
    """Redirect the user to the Innopolis SSO login page."""
    if 'final_redirect_location' in request.args:
        session['final_redirect_location'] = request.args['final_redirect_location']
        if 'frontend_base' in request.args:
            session['frontend_base'] = request.args['frontend_base']

    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.innopolis_sso.authorize_redirect(redirect_uri)


@auth.route('/authorize')
def authorize():
    """Catch the user after the back-redirect and fetch the essential info."""
    try:
        token = oauth.innopolis_sso.authorize_access_token(
            redirect_uri=url_for('auth.authorize', _external=True))
    except AuthlibBaseError:
        abort(401)

    try:
        userinfo = oauth.innopolis_sso.parse_id_token(token)
    except (MissingClaimError, InvalidClaimError):
        abort(401)

    user = db.session.get(Account, userinfo['email'])
    should_be_admin = 'Innopoints_Admins' in userinfo.get('group', [])
    if user is None:
        user = Account(email=userinfo['email'],
                       full_name=userinfo['commonname'],
                       group=userinfo.get('role'),
                       is_admin=should_be_admin)
        db.session.add(user)
        db.session.commit()

    if user.full_name != userinfo['commonname']:
        user.full_name = userinfo['commonname']

    if user.group != userinfo.get('role'):
        user.group = userinfo.get('role')

    if user.is_admin != should_be_admin:
        user.is_admin = should_be_admin

    db.session.commit()

    login_user(user, remember=True)
    session['csrf_token'] = secrets.token_urlsafe()
    session.permanent = True

    final_redirect_uri = session.pop('final_redirect_location', '/')
    frontend_base = session.pop('frontend_base', current_app.config['FRONTEND_BASE'])
    return redirect(urljoin(frontend_base, final_redirect_uri))


@auth.route('/logout')
def logout():
    """Log out the currently signed in user."""
    logout_user()
    return NO_PAYLOAD


@auth.route('/login_cheat/', defaults={'email': 'admin@innopolis.university'})
@auth.route('/login_cheat/<email>')
def login_cheat(email):
    """Bypass OAuth."""
    if current_app.config['ENV'] != 'development':
        abort(400, {'message': 'This endpoint is unavailable.'})
    user = Account.query.get_or_404(email)
    login_user(user, remember=True)
    session['csrf_token'] = secrets.token_urlsafe()

    if 'no_redirect' not in request.args:
        final_redirect_uri = request.args.get('final_redirect_location', '/')
        frontend_base = request.args.get('frontend_base', current_app.config['FRONTEND_BASE'])
        return redirect(urljoin(frontend_base, final_redirect_uri))
    return NO_PAYLOAD
