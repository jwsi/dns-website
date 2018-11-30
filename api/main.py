from flask import Flask, jsonify, abort, url_for, request
from supporting.dynamodb import records as t_records, Attr

from endpoints.check import PUT_check
from classes.errors import ControlledException

# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
application = Flask(__name__)
app = application

optstr = "OPTSTR"

ENTRY_TYPES = {
    "A":     { "ttl": int, "value": [str] },
    "AAAA":  { "ttl": int, "value": [str] },
    "CAA":   { "ttl": int, "value": [{"flags": int, "tag": str, "value": str }]},
    "CNAME": { "ttl": int, "domain": str },
    "MX":    { "ttl": int, "value": [{ "domain": str, "preference": int }] },
    "NAPTR": { "ttl": int, "value": [{ "order": int, "preference": int, "flags": str, "service": str, "regexp": optstr, "replacement": str }]},
    "NS":    { "ttl": int, "value": [str] },
    "SOA":   { "ttl": int, "times": [int], "mname": str, "rname": str },
    "SRV":   { "ttl": int, "value": [{ "priority": int, "weight": int, "port": int, "target": str }] },
    "TXT":   { "ttl": int, "value": str },
}


def check_structure(value, schema):
    if schema == optstr:
        return value is None or isinstance(value, str)
    elif isinstance(schema, dict) and isinstance(value, dict):
        return all(k in value and check_structure(value[k], schema[k]) for k in schema)
    elif isinstance(schema, list) and isinstance(value, list):
        return all(check_structure(c, schema[0]) for c in value)
    elif isinstance(schema, type):
        return isinstance(value, schema)
    else:
        return False


def check_stucture_for_type(struct, type):
    return check_structure(struct, ENTRY_TYPES[type])


class User:
    user_id = "jw"


current_user = User()


@app.route("/r/")
def records():
    resp = t_records.scan(FilterExpression=Attr("user_id").eq(current_user.user_id))
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp["Items"]])


@app.route("/r/<domain>/")
def record(domain):
    response = t_records.get_item(Key={
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

    response = t_records.get_item(Key={
            "domain": domain,
            "user_id": current_user.user_id
        })

    if "Item" not in response:
        abort(404)

    item = response["Item"]
    if request.method == "GET":
        return jsonify(item[type])

    else:
        item[type] = request.get_json()
        if not check_stucture_for_type(item[type], type):
            abort(400)

        ret = t_records.put_item(Item=item)
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
