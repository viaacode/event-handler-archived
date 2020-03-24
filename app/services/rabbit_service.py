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
        self.config = config
        self.retrycount = 1

    def publish_message(self, message: str) -> bool:
        """
        Publishes a message to the queue set in the config.
        
        Arguments:
            message {str} -- Message to be posted.
        """

        credentials = PlainCredentials(
            self.config["environment"]["rabbit"]["username"],
            self.config["environment"]["rabbit"]["password"],
        )
        connection_params = pika.ConnectionParameters(
            host=self.config["environment"]["rabbit"]["host"], credentials=credentials,
        )
        try:
            connection = pika.BlockingConnection(connection_params)
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
        channel.queue_declare(
            queue=self.config["environment"]["rabbit"]["queue"], durable=True
        )
        channel.basic_publish(
            exchange="",
            routing_key=self.config["environment"]["rabbit"]["queue"],
            body=message,
            properties=pika.BasicProperties(delivery_mode=2,),
        )

        connection.close()

        return True
