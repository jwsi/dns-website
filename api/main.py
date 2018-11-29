from flask import Flask, jsonify, abort, url_for, request
from supporting.dynamodb import records

from endpoints.check import PUT_check
from classes.errors import ControlledException

# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
application = Flask(__name__)
app = application

ENTRY_TYPES = {
    "A":     True,
    "AAAA":  True,
    "CAA":   True,
    "CNAME": True,
    "MX":    True,
    "NAPTR": True,
    "NS":    True,
    "SOA":   True,
    "SRV":   True,
    "TXT":   True,
}


class User:
    user_id = "jw"


current_user = User()


@app.route("/r/")
def records():
    resp = records.scan(FilterExpression=Attr("user_id").eq(current_user.user_id))
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp["Items"]])


@app.route("/r/<domain>/")
def record(domain):
    response = records.get_item(Key={
            "domain": domain,
            "user_id": current_user.user_id,
        })

    if "Item" not in response:
        abort(404)

    item = response["Item"]
    return jsonify(item)


@app.route("/r/<domain>/<type>/", methods=["GET", "PUT"])
def record_entry(domain, type):
    if type not in ENTRY_TYPES:
        abort(404)

    response = records.get_item(Key={
            "domain": domain,
            "user_id": current_user.user_id
        })

    if "Item" not in response:
        abort(404)

    item = response["Item"]
    if request.method == "GET":
        return jsonify(item[type])

    else:
        # TODO: validation
        item[type] = request.get_json()
        ret = records.put_item(Item=item)
        return jsonify(ret)


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
