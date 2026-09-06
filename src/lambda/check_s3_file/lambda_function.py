"""
lambda_function.py: S3 Ingestion Gate & File Pre-Validation
Triggered by Step Functions / EventBridge to validate landing payloads
prior to launching high-cost AWS Glue compute.
"""

import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

ALLOWED_EXTENSIONS = {".csv", ".parquet", ".json", ".hl7"}
MIN_FILE_SIZE_BYTES = 32  # Rejects 0-byte or corrupted empty files

def lambda_handler(event, context):
    logger.info(f"Received ingestion event: {json.dumps(event)}")
    
    bucket = event.get("bucket") or os.environ.get("LANDING_BUCKET")
    key = event.get("key")

    if not bucket or not key:
        err_msg = "Missing 'bucket' or 'key' parameter in event payload."
        logger.error(err_msg)
        return {
            "statusCode": 400,
            "isValid": False,
            "reason": err_msg
        }

    # 1. Enforce file extension check
    _, ext = os.path.splitext(key)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        err_msg = f"Rejected file: '{key}'. Extension '{ext}' is not authorized."
        logger.warning(err_msg)
        return {
            "statusCode": 422,
            "isValid": False,
            "bucket": bucket,
            "key": key,
            "reason": err_msg
        }

    # 2. Check S3 object existence and size
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        file_size = response.get("ContentLength", 0)
        last_modified = response.get("LastModified").isoformat()
        content_type = response.get("ContentType", "unknown")

        logger.info(f"File verified: s3://{bucket}/{key} | Size: {file_size} bytes | Type: {content_type}")

        if file_size < MIN_FILE_SIZE_BYTES:
            err_msg = f"File s3://{bucket}/{key} is empty or smaller than {MIN_FILE_SIZE_BYTES} bytes ({file_size} bytes)."
            logger.error(err_msg)
            return {
                "statusCode": 422,
                "isValid": False,
                "bucket": bucket,
                "key": key,
                "file_size": file_size,
                "reason": err_msg
            }

        return {
            "statusCode": 200,
            "isValid": True,
            "bucket": bucket,
            "key": key,
            "file_size": file_size,
            "last_modified": last_modified,
            "content_type": content_type
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"S3 ClientError for s3://{bucket}/{key}: {error_code} - {str(e)}")
        return {
            "statusCode": 404 if error_code == "404" else 500,
            "isValid": False,
            "bucket": bucket,
            "key": key,
            "reason": f"S3 HeadObject failed: {error_code}"
        }