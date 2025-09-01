import logging
import json
import os
from typing import Any
import boto3
import time
from decimal import Decimal

logger = logging.getLogger()
TABLE_NAME = os.environ.get("TABLE_NAME", "records_table")

# TTL setting: expire after 24 hours (86400 seconds)
TTL_DURATION = 86400

def save_to_db(records: list[dict[str, Any]]):
    """Save records to the table.

    Parameters
    ----------
    records: list[dict[str, Any]]
        The data to save to Table.
    """
    # saving records to the Table, Complete the code in here
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    # Calculate expiry timestamp
    expiry_time = int(time.time()) + TTL_DURATION

    with table.batch_writer() as batch:
        for item in records:
            item["ttl"] = expiry_time   # add TTL attribute
            batch.put_item(Item=item)
    print("Records are successfully saved to the DB table")
    logger.info("Records are successfully saved to the DB table %s.", TABLE_NAME)


def lambda_handler(event, context):
    """Process POST request to the API."""
    logger.info(
        'Received %s request to %s endpoint',
        event["httpMethod"],
        event["path"])

    if (orders := event['body']) is not None:
        try:
            orders = json.loads(event["body"], parse_float=Decimal, parse_int=Decimal)
        except Exception as e:
            return {
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps({"errorMessage": f"{e}"})
                }
        logger.info("Orders received: %s.", orders)
        save_to_db(records=orders)

        return {
            "isBase64Encoded": False,
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({"Message": "Successfully saved to DB"})
        }

    return {
        "isBase64Encoded": False,
        "statusCode": 400,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({"errorMessage": "Request body is empty"})
    }
