#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest.mock import patch
import pytest

from app.services.rabbit_service import RabbitService
from pika_mock import Connection as PikaConnection


class TestRabbitService:

    CONFIG_DICT = {
        "environment": {
            "rabbit": {
                "host": "localhost",
                "queue": "archived",
                "exchange": "exchange",
                "username": "guest",
                "password": "guest"
            }
        }
    }

    @pytest.fixture
    def rabbit_service(self):
        return RabbitService(self.CONFIG_DICT)

    @patch('pika.BlockingConnection')
    def test_publish_message(self, conn_mock, rabbit_service):
        # Return mock connection instead of real pika.BlockingConnection
        pika_conn = PikaConnection()
        conn_mock.return_value = pika_conn

        rabbit_service.publish_message("message", "exchange", "routing_key")
        messages = pika_conn.channel_mock.messages
        assert len(messages) == 1
        message = messages[0]
        assert message.body == "message"
        assert message.exchange == "exchange"
        assert message.routing_key == "routing_key"

    @patch('time.sleep')
    @patch('pika.BlockingConnection')
    def test_publish_message_conn_error(self, conn_mock, sleep_mock, rabbit_service):
        # Creating a pika.BlockedConnection throws Exception
        conn_mock.side_effect = Exception

        rabbit_service.publish_message("message", "exchange", "routing_key")
        assert rabbit_service.retrycount == 11
        assert conn_mock.call_count == 11
