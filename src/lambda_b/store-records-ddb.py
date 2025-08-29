# api_lambda.py Handles POST requests, saves to DynamoDB, and sets TTL for 24h.
import json
import boto3
import os
import time
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    """Store records in DynamoDB with 24h TTL."""
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        records = json.loads(event["body"])
        ttl = int(time.time()) + 86400  # 24 hours

        with table.batch_writer() as batch:
            for record in records:
                record["ttl"] = ttl
                batch.put_item(Item=record)
                logger.info("Stored record with TTL: %s", record)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Records inserted successfully"})
        }

    except Exception as e:
        logger.exception("Failed to insert records: %s", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
