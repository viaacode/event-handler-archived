#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Channel:
    """Mocks a pika Channel"""

    def __init__(self):
        self.exchanges = {}
        self.queues = {}

    def basic_publish(self, *args, **kwargs):
        """Puts a message on the in-memory list via the exchange"""

        exchange = kwargs["exchange"]
        routing_key = kwargs["routing_key"]
        self.exchanges[exchange][routing_key].append(kwargs["body"])

    def queue_declare(self, *args, **kwargs):
        """Creates an in-memory list to act as queue"""

        queue = kwargs["queue"]
        if not self.queues.get(queue):
            self.queues[queue] = []

    def exchange_declare(self, *args, **kwargs):
        """Create an in memory dict to act as an exchange"""

        exchange = kwargs["exchange"]
        exchange_type = kwargs["exchange_type"]
        durable = kwargs["durable"]
        if not self.exchanges.get(exchange):
            self.exchanges[exchange] = {
                "exchange_type": exchange_type,
                "durable": durable,
                }

    def queue_bind(self, *args, **kwargs):
        """Map the queue to the exchange"""

        exchange = kwargs["exchange"]
        queue = kwargs["queue"]
        self.exchanges[exchange][queue] = self.queues[queue]


class Connection:
    """Mocks a pika Connection"""

    def __init__(self):
        pass

    def channel(self):
        self.channel_mock = Channel()
        return self.channel_mock

    def close(self):
        pass
