import boto3
from boto3.dynamodb.conditions import Attr


class DB:
    def __init__(self, access_key, secret_key, region):
        self.dynamodb = boto3.resource("dynamodb",
                                  aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key,
                                  region_name=region)
        self.records = self.dynamodb.Table("records")


    def get_record(self, domain, user_id):
        """
        Gets a record object from dynamoDB
        :param domain: domain to query.
        :param user_id: user to query.
        :return: record object or None.
        """
        return self.records.get_item(
            Key={
                "domain": domain,
                "user_id" : user_id
            }
        ).get("Item")


    def get_records_by_user(self, user_id):
        """
        Gets all records owned by a particular user
        :param user_id: user to query.
        :return: list of records or None.
        """
        return self.records.scan(FilterExpression=Attr("user_id").eq(user_id)).get("Items")


    def put_record(self, item):
        """
        Creates or updates a records, and returns the response.
        :param item: The item to put. Must include a valid primary key (user_id+domain).
        :return: the response from dynamoDB
        """
        return self.records.put_item(Item=item)


    def get_live_records_by_domain(self, domain):
        return self.records.scan(
            FilterExpression=Attr('domain').eq(domain) & Attr('live').eq(True)
        ).get("Items")


import os
db = DB(os.environ["AWS_ACCESS_ID"], os.environ["AWS_ACCESS_KEY"], "eu-west-2")
