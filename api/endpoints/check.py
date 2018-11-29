from flask import jsonify
from supporting.dynamodb import records, Attr
from classes.errors import ControlledException
from classes.status import ReturnCode
import whois


def PUT_check(domain, user):
    """
    Checks if a domain is eligible to go live.
    :param domain: Domain to check.
    :param user: Associated user.
    """
    record = _get_record(domain, user)
    correct_ns = {"ns1.uh-dns.com", "ns2.uh-dns.com", "ns3.uh-dns.com", "ns4.uh-dns.com"}
    queried_ns = _get_whois_nameservers(domain)
    if correct_ns != queried_ns:
        raise ControlledException(ReturnCode.CHECK_FAILED)
    _check_no_live_domain(domain)
    # If successful - set the record to be live.
    record["live"] = True
    records.put_item(Item=record)
    return jsonify({
        "status" : ReturnCode.SUCCESS
    })


def _get_record(domain, user):
    """
    Gets a record object from dynamoDB
    :param domain: domain to query.
    :param user: user to query.
    :return: record object.
    """
    try:
        return records.get_item(
            Key={
                "domain": domain,
                "user_id" : user
            }
        )["Item"]
    except KeyError: # Catch records that don't exist.
        raise ControlledException(ReturnCode.DOMAIN_NOT_FOUND)


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
    try:
        already_live = records.scan(
            FilterExpression=Attr('domain').eq(domain) & Attr('live').eq(True)
        )["Items"]
    except KeyError:
        already_live = []
    if len(already_live) > 0:
        raise ControlledException(ReturnCode.DOMAIN_ALREADY_LIVE)