from flask import Flask, jsonify, request, render_template
import flask_menu as menu
from endpoints.check import PUT_check
from endpoints.records import GET_records, GET_record, GET_record_entry, PUT_record_entry
from classes.errors import ControlledException


# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
application = Flask(__name__)
app = application
menu.Menu(app=app)


class User:
    user_id  = "jw"
    fullname = "James Webb"
    is_authenticated = True


current_user = User()


@app.context_processor
def inject_user():
    return dict(current_user=current_user)


def should_return_JSON():
    return "application/json" in request.accept_mimetypes and \
        not "text/html" in request.accept_mimetypes


def split_endpoint(path):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = f(*args, **kwargs)
        if should_return_JSON():
            return jsonify(data)
        else:
            return render_template(path, data=data)

    return decorated_function


@app.route("/")
@menu.register_menu(app, ".", "Home")
def index():
    return render_template("index.html")


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
