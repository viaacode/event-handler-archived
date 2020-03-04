from datetime import datetime
from io import BytesIO
from typing import Tuple

import pika
from flask import Flask, escape, request
from lxml import etree
from viaa.configuration import ConfigParser
from viaa.observability import correlation, logging

from .helpers import xml_builder
from .services import mediahaven_service

app = Flask(__name__)
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)
correlation.initialize(flask=app, logger=logger, pika=pika)


class InvalidEventException(Exception):
    """Exception raised when an event is invalid."""

    pass


def get_event_and_media_id(premis_xml: bytes) -> Tuple[str, str]:
    root = etree.fromstring(premis_xml)

    event: str = root.xpath(
        "string(//p:eventType)", namespaces={"p": "info:lc/xmlns/premis-v2"},
    )
    media_id: str = root.xpath(
        "string(//p:linkingObjectIdentifier[p:linkingObjectIdentifierType = 'MEDIAHAVEN_ID']/p:linkingObjectIdentifierValue)",
        namespaces={"p": "info:lc/xmlns/premis-v2"},
    )

    if not media_id:
        raise InvalidEventException("'MEDIAHAVEN_ID'")
    if not event:
        raise InvalidEventException("'eventType'")

    return event, media_id


def query_mediahaven(media_id: str) -> Tuple[str, str]:
    mediahaven_client = mediahaven_service.MediahavenService(config.config)
    result = mediahaven_client.get_fragment(media_id)

    try:
        pid = result["MediaDataList"][0]["Administrative"]["ExternalId"]
        s3_object_key = result["MediaDataList"][0]["Dynamic"]["s3_object_key"]
    except KeyError as error:
        raise InvalidEventException(str(error))

    return (pid, s3_object_key)


def generate_vrt_xml(pid: str, s3_object_key: str) -> str:
    xml_data_dict = {
        "timestamp": str(datetime.now().isoformat()),
        "file": s3_object_key,
        "pid": pid,
    }

    builder = xml_builder.XMLBuilder()

    builder.build(xml_data_dict)

    return builder.to_string(True)


def publish_message(message: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))

    channel = connection.channel()
    channel.queue_declare(queue="vrt_events", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="vrt_events",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2,),  # make message persistent
    )

    connection.close()


@app.route("/health/live")
def liveness_check() -> str:
    return "OK"


@app.route("/event", methods=["POST"])
def handle_event() -> str:
    premis_xml = request.data

    try:
        (event, media_id) = get_event_and_media_id(premis_xml)
    except InvalidEventException as error:
        logger.warning(f"{error} is not found in the incoming event.", xml=premis_xml)
        return str(error)

    # Check for FLOW.ARCHIVED and it's legacy variant ARCHIVED
    if event != "FLOW.ARCHIVED" and event != "ARCHIVED":
        logger.debug(f"Received '{event}'. Discard it.")
        return f"Received '{event}'. Discard it."

    try:
        (pid, s3_object_key) = query_mediahaven(media_id)
    except InvalidEventException as error:
        logger.warning(
            f"{error} is not found in the mediahaven object.",
            mediahaven_media_id=media_id,
        )

        return str(error)

    message = generate_vrt_xml(pid, s3_object_key)

    publish_message(message)

    logger.info(
        f"essenceArchivedEvent sent for {pid}.",
        mediahaven_event=event,
        mediahaven_media_id=media_id,
        pid=pid,
        s3_object_key=s3_object_key,
    )

    return "OK"
