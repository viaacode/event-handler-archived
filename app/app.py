#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict

import pika
import requests
from flask import Flask, request
from flask_api import status
from lxml.etree import XMLSyntaxError
from viaa.configuration import ConfigParser
from viaa.observability import correlation, logging

from .helpers.xml_helper import XMLBuilder
from .helpers.events_parser import (
    PremisEvent,
    PremisEvents,
    InvalidPremisEventException,
)
from .services.s3 import S3Client
from .services.mediahaven_service import MediahavenService, MediaObjectNotFoundException
from .services.rabbit_service import RabbitService

app = Flask(__name__)
config = ConfigParser()
log = logging.get_logger(__name__, config=config)
correlation.initialize(flask=app, logger=log, pika=pika, requests=requests)


def _get_fragment_metadata(fragment_id: str) -> Dict[str, str]:
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


def _generate_vrt_xml(fragment_info: dict, event_timestamp: str) -> str:
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


def _handle_premis_event(event: PremisEvent):
    """Handle a premis event

    A premis event should have an outcome that is considered successful. If that
    is not the case e.g. "NOK", it will send that event to an "error" exchange for
    reporting reasons.

    In the case of a valid archived event it will be processed further:

    A valid archived means that the event is of type "(RECORDS.)FLOW.ARCHIVED", has
    a fragment ID and status outcome is "OK".

    We'll query MediaHaven to request more information of the media object. This
    information will be packaged as an essenceArchivedEvent and be sent on the queue
    to VRT notifiying them the item has been archived successfully.

    Lastly, it will execute a s3 object-delete so that the archived file will be removed
    from the object store.

    Arguments:
        event {PremisEvent} -- Premis event to handle
    """
    log.debug(
            f"event_type: {event.event_type} / fragment_id: {event.fragment_id} / external_id: {event.external_id}"
        )

    # If the outcome of the premis event is not OK it should not process the event
    if not event.has_valid_outcome:
        log.warning(
            f"Archived event has status: {event.event_outcome} for fragment ID: {event.fragment_id}.",
            fragment_id=event.fragment_id,
            pid=event.external_id
        )
        # Get the fragment metadata to find the organisation
        try:
            fragment = MediahavenService(config.config).get_fragment(event.fragment_id)
            organisation_name = fragment["Administrative"]["OrganisationName"]
        except MediaObjectNotFoundException as e:
            log.warning(e, fragment_id=event.fragment_id, pid=event.external_id)
            organisation_name = "unknown"
        

        # Send a message to an "error" exchange for reporting purposes
        routing_key = f"NOK.{organisation_name}.{event.event_type}".lower()
        exchange = config.config["environment"]["rabbit"]["exchange_nok"]
        RabbitService(config=config.config).publish_message(event.to_string(), exchange, routing_key)
        return

    # is_valid means we have a FragmentID and a "(RECORDS.)FLOW.ARCHIVED" eventType
    if not event.is_valid:
        log.debug(f"Dropping event -> ID:{event.event_id}, type:{event.event_type}")
        return

    fragment_info = _get_fragment_metadata(event.fragment_id)
    if fragment_info:
        message = _generate_vrt_xml(
            fragment_info,
            event.event_datetime,
        )

        s3_bucket = fragment_info["s3_bucket"]
        s3_object_key = fragment_info["s3_object_key"]

        # Send essenceArchivedEvent to the queue
        routing_key = config.config["environment"]["rabbit"]["queue"]
        exchange = config.config["environment"]["rabbit"]["exchange"]
        RabbitService(config=config.config).publish_message(message, exchange, routing_key)

        log.info(
            f"essenceArchivedEvent sent for {event.external_id}.",
            mediahaven_event=event.event_type,
            fragment_id=event.fragment_id,
            pid=event.external_id,
            s3_bucket=s3_bucket,
            s3_object_key=s3_object_key,
        )

        # Delete the s3 object
        S3Client(config_dict=config.config).delete_object(s3_bucket, s3_object_key)


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
        _handle_premis_event(event)

    return "OK", status.HTTP_200_OK
