#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO
from unittest.mock import patch
import os

from flask_api import status
from lxml import etree
from lxml.etree import XMLSyntaxError

from app.app import (
    _generate_vrt_xml,
    _get_fragment_metadata,
    handle_event,
    liveness_check,
)
from tests.resources import single_premis_event, single_premis_event_nok
from app.helpers.events_parser import InvalidPremisEventException, PremisEvents
from app.services.mediahaven_service import MediaObjectNotFoundException


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
    pid = 'a1b2c3'
    md5 = 'abcdef123456'
    object_key = 'an_object_key'
    bucket = 'a_bucket'
    fragment_info = _create_fragment_info_dict(pid, md5, object_key, bucket)
    timestamp = datetime.now().isoformat()
    # Act
    xml = _generate_vrt_xml(fragment_info, timestamp)
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    # Assert
    ns = {"m": "http://www.vrt.be/mig/viaa/api"}
    assert tree.xpath('/m:essenceArchivedEvent/m:pid/text()', namespaces=ns)[0] == pid
    assert tree.xpath('/m:essenceArchivedEvent/m:file/text()', namespaces=ns)[0] == object_key
    assert tree.xpath('/m:essenceArchivedEvent/m:s3bucket/text()', namespaces=ns)[0] == bucket
    assert tree.xpath('/m:essenceArchivedEvent/m:md5sum/text()', namespaces=ns)[0] == md5
    assert tree.xpath('/m:essenceArchivedEvent/m:timestamp/text()', namespaces=ns)[0] == timestamp


def test_generate_vrt_xml_against_xsd():
    # Arrange
    pid = 'a1b2c3'
    md5 = 'abcdef123456'
    object_key = 'an_object_key'
    bucket = 'a_bucket'
    fragment_info = _create_fragment_info_dict(pid, md5, object_key, bucket)
    timestamp = datetime.now().isoformat()
    xml = _generate_vrt_xml(fragment_info, timestamp)
    xsd_file = os.path.join(os.path.dirname(__file__), 'resources', 'essenceArchivedEvent.xsd')
    schema = etree.XMLSchema(file=xsd_file)
    # Act
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    is_xml_valid = schema.validate(tree)
    # Assert
    assert is_xml_valid


def test_liveness_check():
    assert liveness_check() == ('OK', status.HTTP_200_OK)


@patch('app.app.MediahavenService')
def test_get_fragment_metadata(mhs_mock):
    get_fragment_result = {
        "Administrative": {
            "ExternalId": "pid"
        },
        "Dynamic": {
            "s3_object_key": "s3_object_key",
            "s3_bucket": "s3_bucket",
        },
        "Technical": {
            "Md5": "md5"
        }
    }
    mhs_mock.return_value.get_fragment.return_value = get_fragment_result
    metadata = _get_fragment_metadata('fragment_id')
    assert metadata["pid"] == "pid"
    assert metadata["s3_object_key"] == "s3_object_key"
    assert metadata["s3_bucket"] == "s3_bucket"
    assert metadata["md5"] == "md5"


@patch('app.app.MediahavenService')
def test_get_fragment_metadata_key_not_found(mhs_mock):
    # Mock call to MediaHaven to return insufficient information
    get_fragment_result = {
        "Administrative": {
            "ExternalId": "pid"
        }
    }
    mhs_mock.return_value.get_fragment.return_value = get_fragment_result

    metadata = _get_fragment_metadata('fragment_id')
    assert metadata == {}


@patch('app.app.MediahavenService')
def test_get_fragment_metadata_media_not_found(mhs_mock):
    # Mock call to MediaHaven to raise A MediaObjectNotFoundException
    mhs_mock.return_value.get_fragment.side_effect = MediaObjectNotFoundException("denied")
    
    metadata = _get_fragment_metadata('fragment_id')
    assert metadata == {}


@patch('app.app.S3Client')
@patch('app.app.RabbitService')
@patch('app.app._get_fragment_metadata')
@patch('app.app.request')
@patch('app.app.config')
def test_handle_event(
    config_mock,
    post_event_mock,
    get_fragment_metadata_mock,
    rabbit_mock,
    s3_client
):
    # Mock request.data to return a single premis event
    post_event_mock.data = single_premis_event

    # Mock _get_fragment_metadata() to return a metadata-dict
    get_fragment_metadata_mock.return_value = {
            "pid": "pid",
            "md5": "md5",
            "s3_object_key": "s3_object_key",
            "s3_bucket": "s3_bucket"
    }

    result = handle_event()

    # Check if the actual XML message sent to the queue is correct
    assert rabbit_mock().publish_message.call_count == 1
    assert rabbit_mock().publish_message.call_args[0][1] == (
        config_mock.config["environment"]["rabbit"]["exchange"]
    )
    assert rabbit_mock().publish_message.call_args[0][2] == (
        config_mock.config["environment"]["rabbit"]["queue"]
    )
    xml = rabbit_mock().publish_message.call_args[0][0]
    xsd_file = os.path.join(os.path.dirname(__file__), 'resources', 'essenceArchivedEvent.xsd')
    schema = etree.XMLSchema(file=xsd_file)
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    assert schema.validate(tree)

    ns = {"m": "http://www.vrt.be/mig/viaa/api"}
    assert tree.xpath('/m:essenceArchivedEvent/m:pid/text()', namespaces=ns)[0] == "pid"
    assert tree.xpath('/m:essenceArchivedEvent/m:file/text()', namespaces=ns)[0] == "s3_object_key"
    assert tree.xpath('/m:essenceArchivedEvent/m:s3bucket/text()', namespaces=ns)[0] == "s3_bucket"
    assert tree.xpath('/m:essenceArchivedEvent/m:md5sum/text()', namespaces=ns)[0] == "md5"
    assert tree.xpath('/m:essenceArchivedEvent/m:timestamp/text()', namespaces=ns)[0] == "2019-03-30T05:28:40Z"
    assert result == ("OK", status.HTTP_200_OK)

    # Check that it deleted the S3 object
    assert s3_client().delete_object.call_count == 1
    assert s3_client().delete_object.call_args[0][0] == "s3_bucket"
    assert s3_client().delete_object.call_args[0][1] == "s3_object_key"

@patch('app.app.MediahavenService')
@patch('app.app.S3Client')
@patch('app.app.RabbitService')
@patch('app.app._get_fragment_metadata')
@patch('app.app.request')
@patch('app.app.config')
def test_handle_event_outcome_nok(
    config_mock,
    post_event_mock,
    get_fragment_metadata_mock,
    rabbit_mock,
    s3_client,
    mediahaven_mock
):
    # Mock request.data to return a single premis event with outcome "NOK"
    post_event_mock.data = single_premis_event_nok

    # Mock _get_fragment_metadata() to return a metadata-dict
    get_fragment_metadata_mock.return_value = {}

    # Mock get_fragment() to return "test" as organisation name
    mediahaven_mock.return_value.get_fragment.return_value = {"Administrative": {"OrganisationName": "test_org"}}
    

    result = handle_event()

    # Check if there a message send to the "error" exchange
    assert rabbit_mock().publish_message.call_count == 1
    assert "NOK" in rabbit_mock().publish_message.call_args[0][0]
    assert rabbit_mock().publish_message.call_args[0][1] == (
        config_mock.config["environment"]["rabbit"]["exchange_nok"]
    )
    assert rabbit_mock().publish_message.call_args[0][2] == (
        "NOK.test_org.FLOW.ARCHIVED".lower()
    )
    # Should still return "200"
    assert result == ("OK", status.HTTP_200_OK)

    # Check that it didn't delete the S3 object
    assert s3_client().delete_object.call_count == 0


@patch('app.app.request')
@patch.object(PremisEvents, '__init__', side_effect=XMLSyntaxError('', 1, 1, 1))
def test_handle_event_xml_error(premis_events_mock, post_event_mock,):
    # Mock request.data to return irrelevant data
    post_event_mock.data = ''

    result = handle_event()
    assert result[1] == status.HTTP_400_BAD_REQUEST


@patch('app.app.request')
@patch.object(PremisEvents, '__init__', side_effect=InvalidPremisEventException)
def test_handle_event_invalid_premis_event(premis_events_mock, post_event_mock):
    # Mock request.data to return irrelevant data
    post_event_mock.data = ''

    result = handle_event()
    assert result[1] == status.HTTP_400_BAD_REQUEST


@patch('app.app.S3Client')
@patch('app.app.RabbitService')
@patch('app.app._get_fragment_metadata')
@patch('app.app.request')
def test_handle_event_empty_fragment(
    post_event_mock,
    get_fragment_metadata_mock,
    rabbit_mock,
    s3_client
):
    # Mock request.data to return a single premis event
    post_event_mock.data = single_premis_event
    # Mock _get_fragment_metadata() to return an empty-dict
    get_fragment_metadata_mock.return_value = {}

    result = handle_event()

    # Check if there is no message been sent to the queue
    assert rabbit_mock().publish_message.call_count == 0
    # Should still return "200"
    assert result == ("OK", status.HTTP_200_OK)

    # Check that it didn't delete the S3 object
    assert s3_client().delete_object.call_count == 0
