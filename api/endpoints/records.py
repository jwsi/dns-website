from flask import jsonify, abort
from api.classes.db import db


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


def GET_records(user_id):
    resp = db.get_records_by_user(user_id)
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp])


def GET_record(user_id, domain):
    item = db.get_record(domain, user_id)
    if item is None:
        abort(404)

    return jsonify(item)


def GET_record_entry(user_id, domain, type):
    if type not in ENTRY_TYPES:
        abort(404)

    item = db.get_record(domain, user_id)
    if item is None:
        abort(404)

    return jsonify(item[type])


def PUT_record_entry(user_id, domain, type, json):
    if type not in ENTRY_TYPES:
        abort(404)

    item = db.get_record(domain, user_id)
    if item is None:
        abort(404)

    item[type] = json
    if not check_stucture_for_type(item[type], type):
        abort(400)

    ret = db.put_record(item)
    return jsonify(ret)
