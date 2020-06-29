#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
from botocore.exceptions import ClientError

from viaa.configuration import ConfigParser
from viaa.observability import logging

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class S3Client:
    def __init__(self, config_dict: dict = None):
        if not config_dict:
            config_dict = config.config
        self.client = boto3.client(
            's3',
            aws_access_key_id=config_dict["environment"]["s3"]["aws_access_key_id"],
            aws_secret_access_key=config_dict["environment"]["s3"]["aws_secret_access_key"],
            endpoint_url=config_dict["environment"]["s3"]["host"]
        )

    def delete_object(self, s3_bucket: str, s3_key: str):
        try:
            self.client.delete_object(Bucket=s3_bucket, Key=s3_key)
            logger.info(
                f"Deleted s3 object in bucket: {s3_bucket} for key: {s3_key}",
                s3_bucket=s3_bucket,
                s3_key=s3_key
            )
        except ClientError as e:
            logger.error(
                f"Unable to delete s3 object in bucket: {s3_bucket} for key: {s3_key}",
                error=e,
                s3_bucket=s3_bucket,
                s3_key=s3_key
            )
