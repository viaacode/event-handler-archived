#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple, Dict

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
from .services.mediahaven_service import MediahavenService, MediaObjectNotFoundException
from .services.rabbit_service import RabbitService

app = Flask(__name__)
config = ConfigParser()
log = logging.get_logger(__name__, config=config)
correlation.initialize(flask=app, logger=log, pika=pika, requests=requests)


def get_fragment_metadata(fragment_id: str) -> Dict[str, str]:
    """
    Query MediaHaven for the given fragment ID.
    Return the pid, md5, s3 object key and s3 bucket as a dictionary.
    Return empty dictionary if the information is not found or not complete
    for the given ID.
    
    Arguments:
        fragment_id {str} -- Fragment ID for which the information is fetched.

    Returns:
        Dict[str, str] -- Dictionary containing the retrieved metadata.
    """

    mediahaven_client = MediahavenService(config.config)
    try:
        fragment = mediahaven_client.get_fragment(fragment_id)
    except MediaObjectNotFoundException as error:
        log.error(
            f"MediaHaven object not found for ID: {fragment_id}",
            mediahaven_response=f"{error}"
        )
        return {}

    try:
        pid: str = fragment["Administrative"]["ExternalId"]
        s3_object_key: str = fragment["Dynamic"]["s3_object_key"]
        s3_bucket: str = fragment["Dynamic"]["s3_bucket"]
        md5: str = fragment["Technical"]["Md5"]
    except KeyError as error:
        log.warning(
            f"{error} is not found in the MediaHaven object.",
            fragment_id=fragment_id,
            fragment=fragment,
        )
        return {}

    return {
        "pid": pid,
        "md5": md5,
        "s3_object_key": s3_object_key,
        "s3_bucket": s3_bucket,
    }


def generate_vrt_xml(fragment_info: dict, event_timestamp: str) -> str:
    """
    Generates a basic xml for the essenceArchived event.

    Arguments:
        fragment_info {Dict[str,str]} -- Dictionary containing:
            pid {str} -- Pid of the archived item.
            md5 {str} -- The md5 checksum of the archived item.
            s3_bucket {str} -- S3 bucket of the archived item.
            s3_object_key {str} -- S3 object key of the archived item.
        event_timestamp {str} -- Timestamp of archived event.

    Returns:
        str -- EssenceArchived XML with pid, s3 object key, md5 checksum, s3 bucket and timestamp.
    """

    xml_data_dict = {
        "timestamp": event_timestamp,
        "file": fragment_info["s3_object_key"],
        "pid": fragment_info["pid"],
        "s3bucket": fragment_info["s3_bucket"],
        "md5sum": fragment_info["md5"],
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
        log.debug(
            f"event_type: {event.event_type} / fragment_id: {event.fragment_id} / external_id: {event.external_id}"
        )
        # is_valid means we have a FragmentID and a "(RECORDS).FLOW.ARCHIVED" eventType
        if event.is_valid:
            fragment_info = get_fragment_metadata(event.fragment_id)
            if fragment_info:
                message = generate_vrt_xml(
                    fragment_info,
                    event.event_datetime,
                )

                RabbitService(config=config.config).publish_message(message)
                log.info(
                    f"essenceArchivedEvent sent for {event.external_id}.",
                    mediahaven_event=event.event_type,
                    fragment_id=event.fragment_id,
                    pid=event.external_id,
                    s3_bucket=fragment_info["s3_bucket"],
                    s3_object_key=fragment_info["s3_object_key"],
                )
        else:
            log.debug(f"Dropping event -> ID:{event.event_id}, type:{event.event_type}")
    return "OK", status.HTTP_200_OK
