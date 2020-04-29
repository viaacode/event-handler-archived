#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from unittest.mock import patch

from flask_api import status
from lxml import etree
from lxml.etree import XMLSyntaxError


from app.app import (
    generate_vrt_xml,
    liveness_check,
    get_pid_and_s3_object_key,
    handle_event,
)
from tests.resources import single_premis_event
from app.helpers.events_parser import InvalidPremisEventException, PremisEvents


def test_generate_vrt_xml():
    pid = 'a1b2c3'
    object_key = 'an_object_key'
    xml = generate_vrt_xml(pid, object_key)
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    assert tree.xpath('/m:essenceArchivedEvent/m:pid/text()', namespaces={"m":"http://www.vrt.be/mig/viaa/api"})[0] == pid
    assert tree.xpath('/m:essenceArchivedEvent/m:file/text()', namespaces={"m":"http://www.vrt.be/mig/viaa/api"})[0] == object_key


def test_liveness_check():
    assert liveness_check() == ('OK', status.HTTP_200_OK)


@patch('app.app.MediahavenService')
def test_get_pid_and_s3_object_key(mhs_mock):
    get_fragment_result = {
        "MediaDataList": [
            {
                "Administrative": {"ExternalId": "pid"},
                "Dynamic": {"s3_object_key": "s3_object_key"}
            }
        ]
    }
    mhs_mock.return_value.get_fragment.return_value = get_fragment_result
    (pid, s3_object_key) = get_pid_and_s3_object_key('fragment_id')
    assert pid == "pid"
    assert s3_object_key == "s3_object_key"


@patch('pika.BlockingConnection')
@patch('app.app.get_pid_and_s3_object_key')
@patch('app.app.request')
def test_handle_event(post_event_mock, pid_s3_mock, conn_mock):
    # Mock request.data to return a single premis event
    post_event_mock.data = single_premis_event

    # Mock get_pid_and_s3_object_key() to return a pid and s3 object value
    pid_s3_mock.return_value = ("pid", "s3")

    result = handle_event()
    result == ("OK", status.HTTP_200_OK)


@patch('app.app.request')
@patch.object(PremisEvents, '__init__', side_effect=XMLSyntaxError('', 1, 1, 1))
def test_handle_event_xml_error(premis_events_mock, post_event_mock,):
    # Mock request.data to return irrelevant data
    post_event_mock.data = ''

    result = handle_event()
    result[1] == status.HTTP_400_BAD_REQUEST


@patch('app.app.request')
@patch.object(PremisEvents, '__init__', side_effect=InvalidPremisEventException)
def test_handle_event_invalid_premis_event(premis_events_mock, post_event_mock):
    # Mock request.data to return irrelevant data
    post_event_mock.data = ''

    result = handle_event()
    result[1] == status.HTTP_400_BAD_REQUEST
