from flask import jsonify
from api.classes.db import db
from api.classes.errors import ControlledException
from api.classes.status import ReturnCode
import whois


def PUT_check(domain, user):
    """
    Checks if a domain is eligible to go live.
    :param domain: Domain to check.
    :param user: Associated user.
    """
    record = db.get_record(domain, user)
    if record is None:
        raise ControlledException(ReturnCode.DOMAIN_NOT_FOUND)

    correct_ns = {"ns1.uh-dns.com", "ns2.uh-dns.com", "ns3.uh-dns.com", "ns4.uh-dns.com"}
    queried_ns = _get_whois_nameservers(domain)
    if correct_ns != queried_ns:
        raise ControlledException(ReturnCode.CHECK_FAILED)

    _check_no_live_domain(domain)
    # If successful - set the record to be live.
    record["live"] = True
    db.put_record(record)
    return jsonify({
        "status" : ReturnCode.SUCCESS
    })


def _get_whois_nameservers(domain):
    """
    Gets the authorative nameservers for a domain.
    :param domain: domain to check.
    :return: Authorative nameservers for a domain.
    """
    try:
        response = whois.whois(domain[:-1]) # Do WHOIS lookup without trailing .
        ns = {record.lower() for record in response.name_servers}
    except: # No nameservers present
        ns = []
    return ns


def _check_no_live_domain(domain):
    """
    Check that no live domain exists already.
    :param domain: domain to check.
    """
    already_live = db.get_live_records_by_domain(domain)
    if len(already_live) > 0:
        raise ControlledException(ReturnCode.DOMAIN_ALREADY_LIVE)
