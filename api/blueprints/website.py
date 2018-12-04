from flask import Blueprint, render_template, session
from decorators.authentication import requires_auth
import json

website = Blueprint('website', __name__)


@website.route('/dashboard')
@requires_auth("user")
def dashboard():
    """
    Define a function to display the user dashboard page.
    :return:
    """
    return render_template('dashboard.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))


@website.route("/home")
def home():
    """
    Define a function to display the home page.
    :return:
    """
    return render_template('home.html')