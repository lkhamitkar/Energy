# Processes orders (accept/reject), saves accepted ones to S3, and notifies on errors.
import os
import boto3
import requests  # Reserved for notifications
from typing import Any
import datetime as dt
import logging
import json


# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "order-details-energy")

# Slack webhook environment variable (replace with actual endpoint)
# SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "https://example.com/slack-webhook")

""" def notify_failure(message: str):
    Send a notification to Slack-like channel.
    payload = {"CRITICAL": f" Lambda B Failure: {message}"}
    try:
        logger.info("Sending notification: %s", payload)
        # add webhook details here
        requests.post(SLACK_WEBHOOK, json=payload, timeout=3)
    except Exception as e:
        logger.warning("Failed to send Slack notification: %s", str(e))
"""

def save_to_s3(data: dict[str, Any], filename: str):
    """Save data to the S3 bucket with retry logic.

    Parameters
    ----------
    data: dict[str, Any]
        The data to save to the S3 bucket.
    filename: str
        The full object name for the file.
    """
    attempt = 0
    retries = 3
    # exponential backoff base in seconds
    while attempt <= retries:
        try:
            logger.info(f"Attempt {attempt + 1}: Saving order to S3 bucket {BUCKET_NAME} with key {filename}")
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=filename,
                Body=json.dumps(data),
                # ContentType="application/json"
            )
            logger.info("Successfully saved order to S3")
            return
        except Exception as e:
            attempt += 1
            if attempt > retries:
                logger.exception(f"All retries failed. Could not save to S3: {str(e)}")
                raise
            logger.warning(f"Failed to save order (attempt {attempt}/{retries} with exception: {str(e)}). Retrying...")


def lambda_handler(event, context):
    """Process order result."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        orders_list = event["Payload"].get("orders", [])

        if len(orders_list) == 0:
            logger.error("Orders list is empty")
            raise ValueError("Orders list is empty")

        # Save accepted order
        for order in orders_list:
            if order.get("status") == "accepted":
                logger.info(f"Processing accepted order: {order}")
                save_to_s3(data=event, filename=f"orders/order_{dt.datetime.now(dt.timezone.utc).isoformat()}")
            elif order.get("status") == "rejected":
                # slack notification for rejected orders
                logger.info(f"Order rejected: {order}" )
            else:
                logger.warning(f"Unknown order status: {order}")

    except Exception as e:
        logger.exception(f"Lambda B failed: {str(e)}")
        # notify_failure(str(e))
        raise e
