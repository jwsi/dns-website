import os
from flask import Blueprint, session, redirect, url_for
from six.moves.urllib.parse import urlencode
from classes.oauth import Authentication

authentication = Blueprint('authentication', __name__)


@authentication.route('/callback')
def callback_handling():
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
    return redirect('/dashboard')


@authentication.route('/login')
def login():
    """
    Endpoint to authenticate users with auth0.
    :return: Redirect to auth0 login page.
    """
    return Authentication.auth0.authorize_redirect(redirect_uri=os.environ["AUTH0_CALLBACK_URL"], audience='https://uh-dns.eu.auth0.com/userinfo')


@authentication.route('/logout')
def logout():
    """
    Logout a user and delete session data.
    :return:
    """
    session.clear()
    params = {'returnTo': "http://127.0.0.1:5000/home", 'client_id': 'MR3c9T4pmw3wKXm2YfMloTKpeiVhQgpQ'}
    return redirect(Authentication.auth0.api_base_url + '/v2/logout?' + urlencode(params))
