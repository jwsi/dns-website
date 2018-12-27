import socket, dnslib
from flask import Blueprint, request, jsonify, abort
from api import current_user
from api.classes.db import db
from api.classes.errors import ControlledException
from api.classes.status import ReturnCode
from api.decorators.authentication import requires_auth


api = Blueprint('api', __name__)
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


@api.route("/r/")
@requires_auth("user")
def records():
    resp = db.get_records_by_user(current_user.user_id)
    return jsonify([{ "domain": r["domain"], "live": r["live"] } for r in resp])


@api.route("/r/<domain>/", methods=["GET", "PUT"])
@requires_auth("user")
def record(domain):
    item = db.get_record(domain, current_user.user_id)
    if item is None:
        abort(404)

    return jsonify(item)


@api.route("/r/<domain>/<type>/", methods=["GET", "PUT"])
@requires_auth("user")
def record_entry(domain, type):
    if request.method == "GET":
        if type not in ENTRY_TYPES:
            abort(404)

        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        return jsonify(item[type])
    else:
        if type not in ENTRY_TYPES:
            abort(404)

        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        item[type] = request.get_json()
        if not check_stucture_for_type(item[type], type):
            abort(400)

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
    if record is None:
        raise ControlledException(ReturnCode.DOMAIN_NOT_FOUND)
    _check_glue_records(domain)
    _check_no_live_domain(domain)
    # If successful - set the record to be live.
    record["live"] = True
    db.put_record(record)
    return jsonify({
        "status" : ReturnCode.SUCCESS
    })


def _check_glue_records(domain):
    """
    Checks the glue records for a particular name.
    :param domain: Domain to check
    :return: True if glue records are correct. Otherwise a glue error is raised.
    """
    try:
        question = dnslib.DNSRecord.question(domain, qtype="NS")
    except UnicodeError:
        raise ControlledException(ReturnCode.CHECK_FAILED)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0)) # Bind to any available IP and port.
    sock.settimeout(1)
    server = "k.root-servers.net" # First query the RIPE root server
    while True:
        sock.sendto(question.pack(), (socket.gethostbyname(server), 53))
        res = dnslib.DNSRecord.parse(sock.recv(4096))
        nameservers = set([str(record.rdata) for record in res.auth if record.rtype == 2])
        if nameservers == set(["ns1.uh-dns.com.", "ns2.uh-dns.com."]):
            return True
        elif nameservers == set([]) or res.rr != []:
            raise ControlledException(ReturnCode.INCORRECT_GLUE)
        server = nameservers.pop()


def _check_no_live_domain(domain):
    """
    Check that no live domain exists already.
    :param domain: domain to check.
    """
    already_live = db.get_live_records_by_domain(domain)
    if len(already_live) > 0:
        raise ControlledException(ReturnCode.DOMAIN_ALREADY_LIVE)
