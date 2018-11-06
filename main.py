from flask import Flask, jsonify
import boto3, os

# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
# application = Flask(__name__)
# app = application

# Test to demonstrate dynamo db
dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=os.environ["AWS_ACCESS_ID"],
                          aws_secret_access_key=os.environ["AWS_ACCESS_KEY"],
                          region_name='eu-west-2')

table = dynamodb.Table('records')
print(table.creation_date_time)

table.put_item(
   Item={
        'record': 'Im_A_Mug'
    }
)

# ----------------------------------------------------------------------------------------------------------------------

# Start the app.
# if __name__ == "__main__":
#     app.run()
