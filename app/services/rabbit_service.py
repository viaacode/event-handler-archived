#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pika
from pika.credentials import PlainCredentials
from viaa.configuration import ConfigParser
from viaa.observability import logging
import time

config = ConfigParser()
logger = logging.get_logger(__name__, config=config)


class RabbitService(object):
    def __init__(self, config: dict = None, ctx=None):
        self.context = ctx
        self.name = "RabbitMQ Service"
        self.retrycount = 1
        self.host = config["environment"]["rabbit"]["host"]
        credentials = PlainCredentials(
            config["environment"]["rabbit"]["username"],
            config["environment"]["rabbit"]["password"],
        )
        self.connection_params = pika.ConnectionParameters(
            host=self.host, credentials=credentials,
        )

    def publish_message(self, message: str, exchange: str, routing_key: str) -> bool:
        """
        Publishes a message to an exchange with a routing key.

        Arguments:
            message {str} -- Message to be posted.
            exchange {str} -- Exchange to publish to.
            routing_key {str} -- The routing key.
        """

        try:
            connection = pika.BlockingConnection(self.connection_params)
        except Exception as error:
            logger.critical(
                f"Cannot connect to RabbitMq {error}", retry=self.retrycount
            )
            if self.retrycount <= 10:
                time.sleep(60 * self.retrycount)
                self.retrycount = self.retrycount + 1
                self.publish_message(message, exchange, routing_key)
            else:
                logger.critical(
                    f"Message will not be delivered, manual publish needed.",
                    xml=message,
                )
            return False

        channel = connection.channel()

        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2,),
        )

        connection.close()

        return True
