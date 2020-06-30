#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock

from botocore.exceptions import ClientError, EndpointConnectionError
import pytest

from app.services.s3 import S3Client


class TestS3Client:
    CONFIG_DICT = {
        "environment": {
            "s3": {
                "host": "host",
                "aws_access_key_id": "access",
                "aws_secret_access_key": "secret",
            }
        }
    }

    @pytest.fixture
    @patch('boto3.client')
    def s3_client(self, mock_boto_client):
        return S3Client(self.CONFIG_DICT)

    @patch('boto3.client')
    def test_init(self, mock_boto_client):
        S3Client(self.CONFIG_DICT)
        assert mock_boto_client.call_count == 1
        assert mock_boto_client.call_args[0][0] == "s3"
        assert mock_boto_client.call_args[1]["aws_access_key_id"] == "access"
        assert mock_boto_client.call_args[1]["aws_secret_access_key"] == "secret"
        assert mock_boto_client.call_args[1]["endpoint_url"] == "host"

    def test_delete_object_client_error(self, s3_client, caplog):
        # Patch delete_object to return a client error
        mock_boto_client = s3_client.client
        error = ClientError(MagicMock(), MagicMock())
        mock_boto_client.delete_object.side_effect = error

        bucket = "bucket"
        key = "key"
        s3_client.delete_object(bucket, key)

        assert mock_boto_client.delete_object.call_count == 1
        assert caplog.records[0].levelname == "ERROR"
        assert caplog.records[0].error == error
        assert caplog.records[0].s3_bucket == bucket
        assert caplog.records[0].s3_key == key

    def test_delete_object_endpoint_connection_error(self, s3_client, caplog):
        # Patch delete_object to return an endpoint connection error
        mock_boto_client = s3_client.client
        error = EndpointConnectionError(endpoint_url="endpoint")
        mock_boto_client.delete_object.side_effect = error

        bucket = "bucket"
        key = "key"
        s3_client.delete_object(bucket, key)

        assert mock_boto_client.delete_object.call_count == 1
        assert caplog.records[0].levelname == "ERROR"
        assert caplog.records[0].error == error
        assert caplog.records[0].s3_bucket == bucket
        assert caplog.records[0].s3_key == key

    def test_delete_object(self, s3_client, caplog):
        mock_boto_client = s3_client.client
        bucket = "bucket"
        key = "key"
        s3_client.delete_object(bucket, key)

        assert mock_boto_client.delete_object.call_count == 1
        assert caplog.records[0].levelname == "INFO"
        assert caplog.records[0].s3_bucket == bucket
        assert caplog.records[0].s3_key == key
