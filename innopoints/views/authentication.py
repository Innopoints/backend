from flask import abort, current_app, url_for, redirect
from flask_login import login_user, logout_user
from authlib.jose.errors import MissingClaimError, InvalidClaimError

from innopoints.extensions import oauth, db
from innopoints.blueprints import api
from innopoints.models import Account

NO_PAYLOAD = ('', 204)

@api.route('/login', methods=['GET'])
def login():
    """Redirect the user to the Innopolis SSO login page"""
    redirect_uri = url_for('api.authorize', _external=True)
    return oauth.innopolis_sso.authorize_redirect(redirect_uri)


@api.route('/authorize')
def authorize():
    """Catch the user after the back-redirect and fetch the essential info"""
    token = oauth.innopolis_sso.authorize_access_token(
        redirect_uri=url_for('api.authorize', _external=True))
    try:
        userinfo = oauth.innopolis_sso.parse_id_token(token)
    except (MissingClaimError, InvalidClaimError):
        return abort(401)

    user = Account.query.get(userinfo['email'])
    if user is None:
        user = Account(email=userinfo['email'],
                       full_name=userinfo['commonname'],
                       university_status=userinfo['role'],
                       is_admin=current_app.config['IS_ADMIN'](userinfo))
        db.session.add(user)
        db.session.commit()

    if user.full_name != userinfo['commonname']:
        user.full_name = userinfo['commonname']

    if user.university_status != userinfo['role']:
        user.university_status = userinfo['role']

    if user.is_admin != current_app.config['IS_ADMIN'](userinfo):
        user.is_admin = current_app.config['IS_ADMIN'](userinfo)

    db.session.commit()

    login_user(user, remember=True)

    return redirect(url_for('api.list_projects'))


@api.route('/logout')
def logout():
    """Log out the currently signed in user"""
    logout_user()
    return NO_PAYLOAD


@api.route('/login_cheat/', defaults={'index': 0})
@api.route('/login_cheat/<int:index>')
def login_cheat(index):
    """Bypass OAuth"""
    # TODO: remove this
    users = Account.query.all()
    if not users:
        user = Account(email='debug@only.com',
                       full_name='Cheat Account',
                       university_status='hacker',
                       is_admin=True)
        db.session.add(user)
        db.session.commit()
    else:
        user = users[index]
    login_user(user, remember=True)

    return NO_PAYLOAD
