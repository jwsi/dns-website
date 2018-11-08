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
records = dynamodb.Table('records')


def search(domain, q_type):
    """
    Given an IDNA domain string and a record type,
    it will find the corresponding value if it exists.
    :param domain: IDNA domain string.
    :param record_type: Record type (A, AAAA, etc...)
    :return: String representing record value or None.
    """
    logger.info("Request: " + domain + " " + dnslib.QTYPE[q_type])
    rr_list = []
    if q_type == dnslib.QTYPE.NS or q_type == dnslib.QTYPE.ANY:
        rr_list += _ns_search(domain)
    if q_type == dnslib.QTYPE.A or q_type == dnslib.QTYPE.ANY:
        rr_list += _a_search(domain)
    if q_type == dnslib.QTYPE.AAAA or q_type == dnslib.QTYPE.ANY:
        rr_list += _aaaa_search(domain)
    if q_type == dnslib.QTYPE.MX or q_type == dnslib.QTYPE.ANY:
        rr_list += _mx_search(domain)
    if q_type == dnslib.QTYPE.SOA or q_type == dnslib.QTYPE.ANY:
        rr_list += _soa_search(domain)
    if q_type == dnslib.QTYPE.CNAME or q_type == dnslib.QTYPE.ANY:
        rr_list += _cname_search(domain)
    if q_type == dnslib.QTYPE.TXT or q_type == dnslib.QTYPE.ANY:
        rr_list += _txt_search(domain)
    logger.info("Response: " + str(rr_list))
    return rr_list


def _a_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]["A"]
        a_list = []
        ttl = int(record["ttl"])
        for ip in record["value"]:
            a_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.A, rdata=dnslib.A(ip), ttl=ttl))
        return a_list
    except KeyError:
        return []


def _aaaa_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]["AAAA"]
        aaaa_list = []
        ttl = int(record["ttl"])
        for ip in record["value"]:
            aaaa_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.AAAA, rdata=dnslib.AAAA(ip), ttl=ttl))
        return aaaa_list
    except KeyError:
        return []


def _ns_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]["NS"]
        ns_list = []
        ttl = int(record["ttl"])
        for ns in record["value"]:
            ns_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.NS, rdata=dnslib.NS(ns), ttl=ttl))
        return ns_list
    except KeyError:
        return []


def _mx_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain": domain
            }
        )["Item"]["MX"]
        mx_list = []
        ttl = int(record["ttl"])
        for value in record["value"]:
            mx_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.MX, rdata=dnslib.MX(value["domain"], preference=int(value["preference"])), ttl=ttl))
        return mx_list
    except KeyError:
        return []


def _soa_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain": domain
            }
        )["Item"]["SOA"]
        soa_list = []
        ttl = int(record["ttl"])
        times = record["times"]
        times = list(map(lambda time: int(time), times))
        soa_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.SOA, rdata=dnslib.SOA(record["mname"], rname=record["rname"], times=times), ttl=ttl))
        return soa_list
    except KeyError:
        return []


def _cname_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain": domain
            }
        )["Item"]["CNAME"]
        cname_list = []
        ttl = int(record["ttl"])
        cname_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.CNAME, rdata=dnslib.CNAME(record["domain"]), ttl=ttl))
        return cname_list
    except KeyError:
        return []


def _txt_search(domain):
    try:
        record = records.get_item(
            Key={
                "domain" : domain
            }
        )["Item"]["TXT"]
        txt_list = []
        ttl = int(record["ttl"])
        for txt in record["value"]:
            txt_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.TXT, rdata=dnslib.TXT(txt), ttl=ttl))
        return txt_list
    except KeyError:
        return []

