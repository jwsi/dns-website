from flask import Flask, jsonify, abort, url_for, request
import boto3, os
from boto3.dynamodb.conditions import Key, Attr

# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
application = Flask(__name__)
app = application

# Test to demonstrate dynamo db
dynamodb = boto3.resource("dynamodb",
                          aws_access_key_id=os.environ["AWS_ACCESS_ID"],
                          aws_secret_access_key=os.environ["AWS_ACCESS_KEY"],
                          region_name="eu-west-2")

tRecords = dynamodb.Table("records")

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
    resp = tRecords.scan(FilterExpression=Attr("user_id").eq(current_user.user_id))
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp["Items"]])


@app.route("/r/<domain>/")
def record(domain):
    response = tRecords.get_item(Key={
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

    response = tRecords.get_item(Key={
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
        ret = tRecords.put_item(Item=item)
        return jsonify(ret)


# ----------------------------------------------------------------------------------------------------------------------

# Start the app.
if __name__ == "__main__":
    app.run(debug=True)
