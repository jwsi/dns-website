import socket, dnslib
from flask import Blueprint, request, jsonify, abort
from api import current_user
from api.classes.db import db
from api.classes.recordtype import RecordType
from api.classes.errors import ControlledException
from api.classes.status import ReturnCode
from api.decorators.authentication import requires_auth


api = Blueprint('api', __name__)


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
        if type not in RecordType:
            abort(404)

        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        return jsonify(item[type])
    else:
        if type not in RecordType:
            abort(404)

        item = db.get_record(domain, current_user.user_id)
        if item is None:
            abort(404)

        item[type] = request.get_json()
        if not RecordType.check_stucture_for_type(item[type], type):
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
