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
            logger.info("Attempt %s: Saving order to S3 bucket '%s' with key '%s'",
                        attempt + 1, BUCKET_NAME, filename)
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
                logger.exception("All retries failed. Could not save to S3: %s", str(e))
                raise
            logger.warning("Failed to save order (attempt %s/%s). Retrying in %.2f seconds...",
                           attempt, retries)


def lambda_handler(event, context):
    """Process order result."""
    try:
        logger.info("Received event: %s", json.dumps(event))

        # Ensure event has required fields
        if "orders" not in event:
            logger.error("Missing 'orders' field in event")
            raise ValueError("Missing 'orders' field in event")

        if len(event["orders"]) == 0:
            logger.error("Orders list is empty")
            raise ValueError("Orders list is empty")

        # Save accepted order
        for order in event["orders"]:
            if order.get("status") == "accepted":
                logger.info("Processing accepted order: %s", order)
                save_to_s3(data=event, filename=f"orders/order_{dt.datetime.now(dt.timezone.utc).isoformat()}")
            elif order.get("status") == "rejected":
                # slack notification for rejected orders
                logger.info("Order rejected: %s", order)
            else:
                logger.warning("Unknown order status: %s", order)

    except Exception as e:
        logger.exception("Lambda B failed: %s", str(e))
        # notify_failure(str(e))
        raise e
