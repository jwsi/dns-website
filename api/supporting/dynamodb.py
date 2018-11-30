import os, boto3
from boto3.dynamodb.conditions import Key, Attr

# Define the global dynamodb interactor.
dynamodb = boto3.resource("dynamodb",
                          aws_access_key_id=os.environ["AWS_ACCESS_ID"],
                          aws_secret_access_key=os.environ["AWS_ACCESS_KEY"],
                          region_name="eu-west-2")

# Define the records table.
records = dynamodb.Table("records")