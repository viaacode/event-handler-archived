import pika
from pika.credentials import PlainCredentials


class RabbitService(object):
    def __init__(self, config: dict = None, ctx=None):
        self.context = ctx
        self.name = "RabbitMQ Service"
        self.config = config

    def publish_message(self, message: str) -> None:
        """
        Publishes a message to the queue set in the config.
        
        Arguments:
            message {str} -- Message to be posted.
        """

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config["environment"]["rabbit"]["host"],
                    credentials=PlainCredentials(
                        self.config["environment"]["rabbit"]["username"],
                        self.config["environment"]["rabbit"]["password"],
                    ),
                )
            )
        except:
            pass
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
