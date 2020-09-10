#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Message:
    """Convenience class representing a Rabbit message"""
    def __init__(self, body, exchange, routing_key):
        self.body = body
        self.exchange = exchange
        self.routing_key = routing_key

class Channel:
    """Mocks a pika Channel"""
    def __init__(self):
        self.messages = []

    def basic_publish(self, *args, **kwargs):
        """Puts a message on the in-memory list"""
        exchange = kwargs["exchange"]
        routing_key = kwargs["routing_key"]

        self.messages.append(Message(kwargs["body"], exchange, routing_key))


class Connection:
    """Mocks a pika Connection"""
    def __init__(self):
        pass

    def channel(self):
        self.channel_mock = Channel()
        return self.channel_mock

    def close(self):
        pass
