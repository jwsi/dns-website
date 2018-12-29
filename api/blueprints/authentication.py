import os
from flask import Blueprint, session, redirect, url_for, request
from six.moves.urllib.parse import urlencode
from api.classes.oauth import Authentication

authentication = Blueprint('authentication', __name__)


@authentication.route('/callback/')
def callback():
    """
    Define a function to handle auth callbacks.
    :return redirect to dashboard.
    """
    # Handles response from token endpoint
    access_token = Authentication.auth0.authorize_access_token()
    resp = Authentication.auth0.get('userinfo')
    userinfo = resp.json()

    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session["scopes"] = access_token["scope"].split(' ')
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    redirect_uri = request.args.get("redirect_uri") or url_for('website.index')
    return redirect(redirect_uri)


@authentication.route('/login/')
def login():
    """
    Endpoint to authenticate users with auth0.
    :return: Redirect to auth0 login page.
    """
    redirect_uri = url_for('authentication.callback', _external=True, redirect_uri=request.args.get("redirect_uri"))
    return Authentication.auth0.authorize_redirect(redirect_uri=redirect_uri,
                                                   audience='https://uh-dns.eu.auth0.com/userinfo')


@authentication.route('/signup/')
def signup():
    """
    Endpoint to authenticate users with auth0.
    :return: Redirect to auth0 signup page.
    """
    return Authentication.auth0.authorize_redirect(redirect_uri=os.environ["AUTH0_CALLBACK_URL"],
                                                   audience='https://uh-dns.eu.auth0.com/userinfo',
                                                   signUp="true")


@authentication.route('/logout/')
def logout():
    """
    Logout a user and delete session data.
    :return:
    """
    session.clear()
    params = {'returnTo': "http://localhost:5000/", 'client_id': 'MR3c9T4pmw3wKXm2YfMloTKpeiVhQgpQ'}
    return redirect(Authentication.auth0.api_base_url + '/v2/logout?' + urlencode(params))
