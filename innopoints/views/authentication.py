"""Views responsible for authentication.

- GET /login
- GET /authorize
- GET /logout
"""

from flask import abort, current_app, url_for, redirect
from flask_login import login_user, logout_user
from authlib.jose.errors import MissingClaimError, InvalidClaimError

from innopoints.extensions import oauth, db
from innopoints.blueprints import api
from innopoints.models import Account

NO_PAYLOAD = ('', 204)


@api.route('/login')
def login():
    """Redirect the user to the Innopolis SSO login page."""
    try:
        redirect_uri = url_for('api.authorize', _external=True)
        return oauth.innopolis_sso.authorize_redirect(redirect_uri)
    except Exception as exc:
        print(exc)


@api.route('/authorize')
def authorize():
    """Catch the user after the back-redirect and fetch the essential info."""
    token = oauth.innopolis_sso.authorize_access_token(
        redirect_uri=url_for('api.authorize', _external=True))
    try:
        userinfo = oauth.innopolis_sso.parse_id_token(token)
    except (MissingClaimError, InvalidClaimError):
        abort(401)

    user = Account.query.get(userinfo['email'])
    if user is None:
        user = Account(email=userinfo['email'],
                       full_name=userinfo['commonname'],
                       group=userinfo['role'],
                       is_admin=current_app.config['IS_ADMIN'](userinfo))
        db.session.add(user)
        db.session.commit()

    if user.full_name != userinfo['commonname']:
        user.full_name = userinfo['commonname']

    if user.group != userinfo['role']:
        user.group = userinfo['role']

    if user.is_admin != current_app.config['IS_ADMIN'](userinfo):
        user.is_admin = current_app.config['IS_ADMIN'](userinfo)

    db.session.commit()

    login_user(user, remember=True)

    # return redirect(url_for('api.list_projects'))
    # TODO: find a better solution
    return redirect('https://innopoints-frontend.herokuapp.com/')


@api.route('/logout')
def logout():
    """Log out the currently signed in user."""
    logout_user()
    return NO_PAYLOAD


@api.route('/login_cheat/', defaults={'email': 'admin@innopolis.university'})
@api.route('/login_cheat/<email>')
def login_cheat(email):
    """Bypass OAuth."""
    # TODO: remove this
    user = Account.query.get_or_404(email)
    login_user(user, remember=True)

    return NO_PAYLOAD
