from flask import Blueprint, request, jsonify, abort
from api import current_user
from api.classes.db import db
from api.classes.recordtype import RecordType
from api.classes.livechecker import LiveChecker
from api.classes.status import ReturnCode
from api.decorators.authentication import requires_auth


api = Blueprint('api', __name__)


@api.route("/r/")
@requires_auth("user")
def records():
    resp = db.get_records_by_user(current_user.user_id)
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp])


@api.route("/r/<domain>/")
@requires_auth("user")
def record(domain):
    item = db.get_record(domain, current_user.user_id)
    if item is None:
        abort(404)

    return jsonify(item)


@api.route("/r/<domain>/<type>/", methods=["GET", "PUT"])
@requires_auth("user")
def record_entry(domain, type):
    type = RecordType.get(type)
    if type is None:
        abort(404)

    if request.method == "GET":
        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        return jsonify(item[type])

    else:
        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        record_entry = request.get_json()
        if not RecordType.check_stucture_for_type(item[type], type):
            abort(400)

        if not type.validate_put(item, record_entry):
            abort(400)

        item[type] = record_entry
        ret = db.put_record(item)
        return jsonify(ret)


@api.route("/r/<domain>/check/", methods=["GET"])
@requires_auth("user")
def domain_check(domain):
    """
    Checks if a domain is eligible to go live.
    :param domain: Domain to check.
    :param user: Associated user.
    """
    record = db.get_record(domain, current_user.user_id)
    if not LiveChecker.check(record, domain):
        return jsonify({ "status": ReturnCode.UNKNOWN })

    record["live"] = True
    db.put_record(record)
    return jsonify({
        "status" : ReturnCode.SUCCESS
    })
