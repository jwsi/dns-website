import boto3, os, logging, dnslib

# Set global logging level.
logging.basicConfig(level=logging.INFO)
# create logger with 'DNS Request'.
logger = logging.getLogger("DNS")
logger.setLevel(logging.INFO)

# Define DynamoDB interaction system.
dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=os.environ["AWS_ACCESS_ID"],
                          aws_secret_access_key=os.environ["AWS_ACCESS_KEY"],
                          region_name='eu-west-2')
# Define the record table.
a_records = dynamodb.Table('a_records')
ns_records = dynamodb.Table('ns_records')


def search(domain, q_type):
    """
    Given an IDNA domain string and a record type,
    it will find the corresponding value if it exists.
    :param domain: IDNA domain string.
    :param record_type: Record type (A, AAAA, etc...)
    :return: String representing record value or None.
    """
    if q_type == dnslib.QTYPE.NS:
        return ns_search(domain)
    elif q_type == dnslib.QTYPE.A:
        return a_search(domain)
    return []


def a_search(domain):
    logger.info("Request: " + domain + " A")
    try:
        record = a_records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]
        logger.info("Response: " + str(record["A"]))
        a_list = []
        ttl = int(record["TTL"])
        for ip in record["A"]:
            a_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.A, rdata=dnslib.A(ip), ttl=ttl))
        return a_list
    except KeyError:
        logger.info("Response: UNBOUND")
        return []


def ns_search(domain):
    logger.info("Request: " + domain + " NS")
    try:
        record = ns_records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]
        logger.info("Response: " + str(record["NS"]))
        ns_list = []
        ttl = int(record["TTL"])
        for idna in record["NS"]:
            ns_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.NS, rdata=dnslib.NS(idna), ttl=ttl))
        return ns_list
    except KeyError:
        logger.info("Response: UNBOUND")
        return []

