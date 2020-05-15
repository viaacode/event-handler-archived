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
        self.queue = config["environment"]["rabbit"]["queue"]
        self.exchange = config["environment"]["rabbit"]["exchange"]
        credentials = PlainCredentials(
            config["environment"]["rabbit"]["username"],
            config["environment"]["rabbit"]["password"],
        )
        self.connection_params = pika.ConnectionParameters(
            host=self.host, credentials=credentials,
        )

    def publish_message(self, message: str) -> bool:
        """
        Publishes a message to the queue set in the config.

        Arguments:
            message {str} -- Message to be posted.
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
                self.publish_message(message)
            else:
                logger.critical(
                    f"Message will not be delivered, manual publish needed.",
                    xml=message,
                )
            return False

        channel = connection.channel()

        # Declare queue, exchange and bind the queue to the exchange
        channel.queue_declare(queue=self.queue, durable=True)
        channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
        channel.queue_bind(
            exchange=self.exchange, queue=self.queue, routing_key=self.queue
        )

        channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.queue,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2,),
        )

        connection.close()

        return True
