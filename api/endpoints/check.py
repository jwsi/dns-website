from flask import jsonify
from supporting.dynamodb import records, Attr
from classes.errors import ControlledException
from classes.status import ReturnCode
import dns.resolver


def PUT_check(domain, user):
    """
    Checks if a domain is eligible to go live.
    :param domain: Domain to check.
    :param user: Associated user.
    """
    try:
        record = records.get_item(
            Key={
                "domain": domain,
                "user_id" : user
            }
        )["Item"]
    except KeyError: # Catch records that don't exist.
        raise ControlledException(ReturnCode.DOMAIN_NOT_FOUND)
    correct_ns = {"ns1.ultra-horizon.com", "ns2.ultra-horizon.com"}
    queried_ns = set()
    try:
        answers = dns.resolver.query(record["domain"], 'NS')
    except: # No nameservers present.
        answers = []
    for rdata in answers:
        queried_ns.add(rdata.to_text())
    if correct_ns != queried_ns:
        raise ControlledException(ReturnCode.CHECK_FAILED)
    try:
        already_live = records.scan(
            FilterExpression=Attr('domain').eq(domain) & Attr('live').eq(True)
        )["Items"]
    except KeyError:
        already_live = []
    if len(already_live) > 0:
        raise ControlledException(ReturnCode.DOMAIN_ALREADY_LIVE)
    # If successful - set the record to be live.
    record.live = True
    records.put_item(Item=record)
    return jsonify({
        "status" : ReturnCode.SUCCESS
    })