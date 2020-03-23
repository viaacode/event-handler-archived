#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple

import pika
import requests
from flask import Flask, escape, request
from flask_api import status
from lxml import etree
from lxml.etree import XMLSyntaxError
from requests.exceptions import RequestException
from viaa.configuration import ConfigParser
from viaa.observability import correlation, logging

from .helpers.xml_helper import XMLBuilder
from .helpers.events_parser import PremisEvents, InvalidPremisEventException
from .services.mediahaven_service import MediahavenService
from .services.rabbit_service import RabbitService

app = Flask(__name__)
config = ConfigParser()
log = logging.get_logger(__name__, config=config)
correlation.initialize(flask=app, logger=log, pika=pika, requests=requests)


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
        log.warning(
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
    return "OK", status.HTTP_200_OK


@app.route("/event", methods=["POST"])
def handle_event() -> str:
    # Get and parse the incoming event(s)
    log.debug(request.data)
    try:
        premis_events = PremisEvents(request.data)
    except (XMLSyntaxError, InvalidPremisEventException) as e:
        log.error(e)
        return f"NOK: {e}", status.HTTP_400_BAD_REQUEST

    log.debug(f"Events in payload: {len(premis_events.events)}")
    for event in premis_events.events:
        log.debug(f"event_type: {event.event_type} / fragment_id: {event.fragment_id} / external_id: {event.external_id}")
        # is_valid means we have a FragmentID and a "FLOW.ARCHIVED" eventType
        if event.is_valid:
            (pid, s3_object_key) = get_pid_and_s3_object_key(event.fragment_id)
            message = generate_vrt_xml(event.external_id, s3_object_key)
            RabbitService(config=config.config).publish_message(message)
            log.info(
                f"essenceArchivedEvent sent for {pid}.",
                mediahaven_event=event.event_type,
                fragment_id=event.fragment_id,
                pid=event.external_id,
                s3_object_key=s3_object_key,
            )
        else:
            log.debug(f"Dropping event -> ID:{event.event_id}, type:{event.event_type}")
    return "OK", status.HTTP_200_OK
