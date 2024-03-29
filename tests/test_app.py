#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from lxml import etree
from lxml.etree import XMLSyntaxError
from mediahaven.mediahaven import MediaHavenException
from mediahaven.mocks.base_resource import MediaHavenSingleObjectJSONMock

from app.app import _generate_vrt_xml, _get_fragment_metadata, app
from app.helpers.events_parser import InvalidPremisEventException, PremisEvents
from tests.resources import single_premis_event, single_premis_event_nok

# Create a FastAPI test client
client = TestClient(app)


def _create_fragment_info_dict(pid: str, md5: str, s3_object_key: str, s3_bucket: str):
    fragment_info = {
        "pid": pid,
        "md5": md5,
        "s3_object_key": s3_object_key,
        "s3_bucket": s3_bucket,
    }
    return fragment_info


def test_generate_vrt_xml():
    # Arrange
    pid = "a1b2c3"
    md5 = "abcdef123456"
    object_key = "an_object_key"
    bucket = "a_bucket"
    fragment_info = _create_fragment_info_dict(pid, md5, object_key, bucket)
    timestamp = datetime.now().isoformat()
    # Act
    xml = _generate_vrt_xml(fragment_info, timestamp)
    tree = etree.parse(BytesIO(xml.encode("utf-8")))
    # Assert
    ns = {"m": "http://www.vrt.be/mig/viaa/api"}
    assert tree.xpath("/m:essenceArchivedEvent/m:pid/text()", namespaces=ns)[0] == pid
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:file/text()", namespaces=ns)[0]
        == object_key
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:s3bucket/text()", namespaces=ns)[0]
        == bucket
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:md5sum/text()", namespaces=ns)[0] == md5
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:timestamp/text()", namespaces=ns)[0]
        == timestamp
    )


def test_generate_vrt_xml_against_xsd():
    # Arrange
    pid = "a1b2c3"
    md5 = "abcdef123456"
    object_key = "an_object_key"
    bucket = "a_bucket"
    fragment_info = _create_fragment_info_dict(pid, md5, object_key, bucket)
    timestamp = datetime.now().isoformat()
    xml = _generate_vrt_xml(fragment_info, timestamp)
    xsd_file = os.path.join(
        os.path.dirname(__file__), "resources", "essenceArchivedEvent.xsd"
    )
    schema = etree.XMLSchema(file=xsd_file)
    # Act
    tree = etree.parse(BytesIO(xml.encode("utf-8")))
    is_xml_valid = schema.validate(tree)
    # Assert
    assert is_xml_valid


def test_liveness_check():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.text == "OK"


@patch("app.app.MediaHaven")
def test_get_fragment_metadata(
    mh_mock,
):
    fragment_metadata = {
        "Administrative": {"ExternalId": "pid"},
        "Dynamic": {
            "s3_object_key": "s3_object_key",
            "s3_bucket": "s3_bucket",
        },
        "Technical": {"Md5": "md5"},
    }
    result = MediaHavenSingleObjectJSONMock(fragment_metadata)
    mh_mock.records.get.return_value = result
    metadata = _get_fragment_metadata("fragment_id", mh_mock)
    assert metadata["pid"] == "pid"
    assert metadata["s3_object_key"] == "s3_object_key"
    assert metadata["s3_bucket"] == "s3_bucket"
    assert metadata["md5"] == "md5"


@patch("app.app.MediaHaven")
def test_get_fragment_metadata_key_not_found(
    mh_mock,
):
    # Mock call to MediaHaven to return insufficient information
    fragment_metadata = {"Administrative": {"ExternalId": "pid"}}
    result = MediaHavenSingleObjectJSONMock(fragment_metadata)

    mh_mock.records.get.return_value = result
    metadata = _get_fragment_metadata("fragment_id", mh_mock)
    assert metadata == {}


@patch("app.app.MediaHaven")
def test_get_fragment_metadata_media_not_found(mh_mock):
    # Mock call to MediaHaven to raise A MediaObjectNotFoundException
    mh_mock.records.get.side_effect = MediaHavenException("denied")

    metadata = _get_fragment_metadata("fragment_id", mh_mock)
    assert metadata == {}


@patch("app.app.S3Client")
@patch("app.app.RabbitService")
@patch("app.app._get_fragment_metadata")
@patch("app.app.config")
def test_handle_event(config_mock, get_fragment_metadata_mock, rabbit_mock, s3_client):
    # Mock _get_fragment_metadata() to return a metadata-dict
    get_fragment_metadata_mock.return_value = {
        "pid": "pid",
        "md5": "md5",
        "s3_object_key": "s3_object_key",
        "s3_bucket": "s3_bucket",
    }

    result = client.post("/event", data=single_premis_event)

    # Check if the actual XML message sent to the queue is correct
    assert rabbit_mock().publish_message.call_count == 1
    assert rabbit_mock().publish_message.call_args[0][1] == (
        config_mock.config["environment"]["rabbit"]["exchange"]
    )
    assert rabbit_mock().publish_message.call_args[0][2] == (
        config_mock.config["environment"]["rabbit"]["queue"]
    )
    xml = rabbit_mock().publish_message.call_args[0][0]
    xsd_file = os.path.join(
        os.path.dirname(__file__), "resources", "essenceArchivedEvent.xsd"
    )
    schema = etree.XMLSchema(file=xsd_file)
    tree = etree.parse(BytesIO(xml.encode("utf-8")))
    assert schema.validate(tree)

    ns = {"m": "http://www.vrt.be/mig/viaa/api"}
    assert tree.xpath("/m:essenceArchivedEvent/m:pid/text()", namespaces=ns)[0] == "pid"
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:file/text()", namespaces=ns)[0]
        == "s3_object_key"
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:s3bucket/text()", namespaces=ns)[0]
        == "s3_bucket"
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:md5sum/text()", namespaces=ns)[0] == "md5"
    )
    assert (
        tree.xpath("/m:essenceArchivedEvent/m:timestamp/text()", namespaces=ns)[0]
        == "2019-03-30T05:28:40Z"
    )
    assert result.status_code == 202
    assert result.json() == {"message": "Processing 1 event(s) in the background."}

    # Check that it deleted the S3 object
    assert s3_client().delete_object.call_count == 1
    assert s3_client().delete_object.call_args[0][0] == "s3_bucket"
    assert s3_client().delete_object.call_args[0][1] == "s3_object_key"


@patch("app.app.MediaHaven")
@patch("app.app.S3Client")
@patch("app.app.RabbitService")
@patch("app.app.ROPCGrant")
@patch("app.app.config")
def test_handle_event_outcome_nok(
    config_mock, ropc_grant_mock, rabbit_mock, s3_client, mediahaven_mock
):
    # Mock get_fragment() to return "test" as organisation name
    fragment_metadata = {"Administrative": {"OrganisationName": "test_org"}}
    result = MediaHavenSingleObjectJSONMock(fragment_metadata)
    mediahaven_mock().records.get.return_value = result

    with TestClient(app) as mh_client:
        result = mh_client.post("/event", data=single_premis_event_nok)

    # Check if there a message send to the "error" exchange
    assert rabbit_mock().publish_message.call_count == 1
    assert "NOK" in rabbit_mock().publish_message.call_args[0][0]
    assert rabbit_mock().publish_message.call_args[0][1] == (
        config_mock.config["environment"]["rabbit"]["exchange_nok"]
    )
    assert rabbit_mock().publish_message.call_args[0][2] == (
        "NOK.test_org.RECORDS.FLOW.ARCHIVED".lower()
    )
    # Should still return "202"
    assert result.status_code == 202
    assert result.json() == {"message": "Processing 1 event(s) in the background."}

    # Check that it didn't delete the S3 object
    assert s3_client().delete_object.call_count == 0


@patch.object(
    PremisEvents,
    "__init__",
    side_effect=XMLSyntaxError(
        "Document is empty, line 1, column 1", 1, 1, 1, "<string>"
    ),
)
def test_handle_event_xml_error(premis_events_mock):
    result = client.post("/event", data="")
    assert result.status_code == 400
    assert result.json() == {
        "detail": "NOK: Document is empty, line 1, column 1 (<string>, line 1)"
    }


@patch.object(
    PremisEvents, "__init__", side_effect=InvalidPremisEventException("Invalid event")
)
def test_handle_event_invalid_premis_event(premis_events_mock):
    result = client.post("/event", data="")
    assert result.status_code == 400
    assert result.json() == {"detail": "NOK: Invalid event"}


@patch("app.app.S3Client")
@patch("app.app.RabbitService")
@patch("app.app._get_fragment_metadata")
def test_handle_event_empty_fragment(
    get_fragment_metadata_mock, rabbit_mock, s3_client
):
    # Mock _get_fragment_metadata() to return an empty-dict
    get_fragment_metadata_mock.return_value = {}

    result = client.post("/event", data=single_premis_event)

    # Check if there is no message been sent to the queue
    assert rabbit_mock().publish_message.call_count == 0
    # Should still return "202"
    assert result.status_code == 202
    assert result.json() == {"message": "Processing 1 event(s) in the background."}

    # Check that it didn't delete the S3 object
    assert s3_client().delete_object.call_count == 0


@patch("app.app.MediaHaven")
@patch("app.app.PremisEvents")
@patch("app.app._handle_premis_event")
@patch("app.app.ROPCGrant")
@patch("app.app.config.config")
def test_handle_event_init_client(
    config_mock,
    ropc_grant_mock,
    handle_premis_event_mock,
    premis_events_mock,
    mediahaven_mock,
):
    """Test if mediahaven client gets initialized via dependency injection"""
    # Mock a premis event
    premis_event = MagicMock()
    premis_events_mock().events = [premis_event]

    with TestClient(app) as mh_client:
        mh_client.post("/event", data="")

    # Check if _handle_premis_event got the initialized mediahaven mock as an arg
    handle_premis_event_mock.assert_called_once_with(
        premis_event, mediahaven_mock.return_value
    )
