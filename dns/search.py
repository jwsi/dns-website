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
table = dynamodb.Table('records')


def search(domain, record_type):
    """
    Given an IDNA domain string and a record type,
    it will find the corresponding value if it exists.
    :param domain: IDNA domain string.
    :param record_type: Record type (A, AAAA, etc...)
    :return: String representing record value or None.
    """
    logger.info("Request: " + domain + " " + record_type)
    try:
        record = table.get_item(
            Key={
                'record': domain
            }
        )["Item"]
        logger.info("Response: " + record[record_type])
        return _format_record(record[record_type], record_type)
    except KeyError:
        logger.info("Response: UNBOUND")
        return None


def _format_record(value, record_type):
    if record_type == "A":
        return dnslib.A(value)


def get_authority():
    pass