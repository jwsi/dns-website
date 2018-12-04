import os
from flask import Flask, jsonify, request, session
from endpoints.check import PUT_check
from endpoints.records import GET_records, GET_record, GET_record_entry, PUT_record_entry
from classes.errors import ControlledException
from classes.oauth import Authentication
from blueprints.authentication import authentication
from blueprints.website import website

# Define the Flask name as "app".
application = Flask(__name__)
app = application

# Setup the authentication system and define the secret session key.
Authentication.initialize(app)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Register blueprints for the application here.
app.register_blueprint(authentication)
app.register_blueprint(website)



class User:
    user_id = "jw"


current_user = User()


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

# ----------------------------------------------------------------------------------------------------------------------

# Start the app.
if __name__ == "__main__":
    app.run(debug=True)
