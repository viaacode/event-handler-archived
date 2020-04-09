#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Channel:
    """Mocks a pika Channel"""

    def __init__(self):
        self.queues = {}

    def basic_publish(self, *args, **kwargs):
        """Puts a message on the in-memory list"""

        self.queues[kwargs["routing_key"]].append(kwargs["body"])

    def queue_declare(self, *args, **kwargs):
        """Creates an in-memory list to act as queue"""

        queue = kwargs["queue"]
        if not self.queues.get(queue):
            self.queues[queue] = []


class Connection:
    """Mocks a pika Connection"""

    def __init__(self):
        pass

    def channel(self):
        self.channel_mock = Channel()
        return self.channel_mock

    def close(self):
        pass
