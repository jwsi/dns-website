import os
from flask import Flask, jsonify, session
import flask_menu as menu
from flask_wtf.csrf import CSRFProtect

# Define the Flask name as "app".
app = Flask(__name__)
application = app
menu.Menu(app=app)
csrf = CSRFProtect(app)


from .classes.customjsonencoder import CustomJSONEncoder
app.json_encoder = CustomJSONEncoder


from .classes.oauth import Authentication

# Setup the authentication system and define the secret session key.
Authentication.initialize(app)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


class User:
    user_id  = "Guest"
    fullname = ""
    is_authenticated = False


current_user = User()


@app.before_request
def update_current_user():
    global current_user

    if "profile" in session:
        current_user.user_id = session["profile"]["user_id"]
        current_user.fullname = session["profile"]["name"]
        current_user.is_authenticated = True
    else:
        current_user.user_id = "guest"
        current_user.fullname = "Guest"
        current_user.is_authenticated = False


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


from .classes.errors import ControlledException
from . import blueprints


@app.errorhandler(ControlledException)
def controlled_exception_handler(controlled_exception):
    """
    Controlled exception handler.
    :param controlled_exception: Controlled exception to handle.
    """
    return jsonify({
        "status" : controlled_exception.status
    })
