from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple

import pika
import requests
from flask import Flask, escape, request
from lxml import etree
from requests.exceptions import RequestException
from viaa.configuration import ConfigParser
from viaa.observability import correlation, logging

from .helpers.xml_helper import XMLBuilder
from .services.mediahaven_service import MediahavenService
from .services.rabbit_service import RabbitService

app = Flask(__name__)
config = ConfigParser()
logger = logging.get_logger(__name__, config=config)
correlation.initialize(flask=app, logger=logger, pika=pika, requests=requests)


def get_event_and_fragment_id(premis_xml: bytes) -> Tuple[str, str]:
    """
    Extracts the Mediahaven event and media id from an incoming premis event using xpath. Returns empty strings
    
    Arguments:
        premis_xml {bytes} -- Body of the incoming webhook from Mediahaven
    
    Raises:
        InvalidEventException: Raised when either the media id or the eventname is not found.
    
    Returns:
        Tuple[str, str] -- Tuple of the eventname and Mediahaven media id.
    """

    root = etree.fromstring(premis_xml)

    event: str = root.xpath(
        "string(//p:eventType)", namespaces={"p": "info:lc/xmlns/premis-v2"},
    )
    fragment_id: str = root.xpath(
        "string(//p:linkingObjectIdentifier[p:linkingObjectIdentifierType = 'MEDIAHAVEN_ID']/p:linkingObjectIdentifierValue)",
        namespaces={"p": "info:lc/xmlns/premis-v2"},
    )

    if not fragment_id or not event:
        logger.warning(
            "'MEDIAHAVEN_ID' or 'eventType' is missing in the mediahaven event.",
            premis_xml=premis_xml,
        )

    return event, fragment_id


def get_pid_and_s3_object_key(fragment_id: str) -> Tuple[str, str]:
    """
    Query Mediahaven for the given fragment id and return the pid and s3 object key if available, otherwise returns empty strings.
    
    Arguments:
        fragment_id {str} -- Fragment id for which the pid and s3 object key needs to be found. 
    
    Raises:
        KeyError: Raised when no fragment is found or it lacks and s3 object key.
    
    Returns:
        Tuple[str, str] -- Tuple of the pid and s3 object key. (pid, s3_object_key)
    """

    mediahaven_client = MediahavenService(config.config)
    fragment = mediahaven_client.get_fragment(fragment_id)
    try:
        pid: str = fragment["MediaDataList"][0]["Administrative"]["ExternalId"]
        s3_object_key: str = fragment["MediaDataList"][0]["Dynamic"]["s3_object_key"]
    except KeyError as error:
        logger.warning(
            f"{error} is not found in the mediahaven object.",
            fragment_id=fragment_id,
            fragment=fragment,
        )
        return ("", "")
    return (pid, s3_object_key)


def generate_vrt_xml(pid: str, s3_object_key: str) -> str:
    """
    Generates a basic xml for the essenceArchived event.
    
    Arguments:
        pid {str} -- Pid of the archived item.
        s3_object_key {str} -- S3 object key of the archived item.
    
    Returns:
        str -- EssenceArchived XML with pid, s3 object key and timestamp.
    """

    xml_data_dict = {
        "timestamp": str(datetime.now().isoformat()),
        "file": s3_object_key,
        "pid": pid,
    }

    builder = XMLBuilder()
    builder.build(xml_data_dict)
    xml = builder.to_string(True)

    return xml


@app.route("/health/live")
def liveness_check() -> str:
    return "OK"


@app.route("/event", methods=["POST"])
def handle_event() -> str:
    premis_xml = request.data
    (event, fragment_id) = get_event_and_fragment_id(premis_xml)

    if not fragment_id or event != "FLOW.ARCHIVED":
        return "NOK"

    (pid, s3_object_key) = get_pid_and_s3_object_key(fragment_id)

    if not pid or not s3_object_key:
        return "NOK"

    message = generate_vrt_xml(pid, s3_object_key)

    RabbitService(config=config.config).publish_message(message)

    logger.info(
        f"essenceArchivedEvent sent for {pid}.",
        mediahaven_event=event,
        fragment_id=fragment_id,
        pid=pid,
        s3_object_key=s3_object_key,
    )

    return "OK"
