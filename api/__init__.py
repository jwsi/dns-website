import os
from flask import Flask, jsonify, request, session
import flask_menu as menu

# Define the Flask name as "app".
app = Flask(__name__)
application = app
menu.Menu(app=app)


from .classes.oauth import Authentication

# Setup the authentication system and define the secret session key.
Authentication.initialize(app)
app.secret_key = os.environ["FLASK_SECRET_KEY"]




class User:
    user_id  = "Guest"
    fullname = ""
    is_authenticated = False


current_user = User()



from .endpoints.check import PUT_check
from .endpoints.records import GET_records, GET_record, GET_record_entry, PUT_record_entry
from .classes.errors import ControlledException
from .blueprints.authentication import authentication
from .blueprints.website import website

# Register blueprints for the application here.
app.register_blueprint(authentication)
app.register_blueprint(website)


@app.context_processor
def inject_user():
    current_user = User()
    if "profile" in session:
        current_user.user_id = session["profile"]["user_id"]
        current_user.fullname = session["profile"]["name"]
        current_user.is_authenticated = True

    return dict(current_user=current_user)


@app.route("/r/")
def records():
    return GET_records(current_user.user_id)


@app.route("/r/<domain>/", methods=["GET", "PUT"])
def record(domain):
    return GET_record(current_user.user_id, domain)


@app.route("/r/<domain>/<type>/", methods=["GET", "PUT"])
def record_entry(domain, type):
    if request.method == "GET":
        return GET_record_entry(current_user.user_id, domain, type)
    else:
        return PUT_record_entry(current_user.user_id, domain, type, request.get_json())


@app.route("/r/<domain>/check/", methods=["PUT"])
def domain_check(domain):
    return PUT_check(domain, current_user.user_id)


@app.errorhandler(ControlledException)
def controlled_exception_handler(controlled_exception):
    """
    Controlled exception handler.
    :param controlled_exception: Controlled exception to handle.
    """
    return jsonify({
        "status" : controlled_exception.status
    })
