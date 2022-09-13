#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from lxml.etree import XMLSyntaxError, fromstring as parse_xml_string

from tests.resources import (
        single_premis_event,
        single_premis_event_nok,
        multi_premis_event,
        invalid_premis_event,
        invalid_xml_event,
        single_event_no_external_id,
        single_premis_event_archived_on_tape,
        single_premis_event_archived_flow,
)
from app.helpers.events_parser import (
    PremisEvent,
    PremisEvents,
    InvalidPremisEventException,
)

def test_single_event():
    p = PremisEvents(single_premis_event)
    assert len(p.events) == 1
    assert p.events[0].event_id == "111"
    assert p.events[0].event_detail == "Ionic Defibulizer"
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "RECORDS.FLOW.ARCHIVED"
    assert p.events[0].event_outcome == "OK"
    assert p.events[0].event_datetime == "2019-03-30T05:28:40Z"
    assert p.events[0].external_id == "a1"
    assert p.events[0].is_valid
    assert p.events[0].has_valid_outcome

def test_single_event_nok():
    p = PremisEvents(single_premis_event_nok)
    assert len(p.events) == 1
    assert p.events[0].event_type == "RECORDS.FLOW.ARCHIVED"
    assert p.events[0].event_outcome == "NOK"
    assert p.events[0].is_valid
    assert not p.events[0].has_valid_outcome

@pytest.mark.parametrize(
    "resource, event_type",
    [
        (single_premis_event_archived_flow, "FLOW.ARCHIVED",),
        (single_premis_event_archived_on_tape, "RECORDS.FLOW.ARCHIVED_ON_TAPE",),
    ],
)
def test_single_event_invalid(resource, event_type):
    p = PremisEvents(resource)
    assert len(p.events) == 1
    assert p.events[0].event_type == event_type
    assert p.events[0].event_outcome == "OK"
    assert not p.events[0].is_valid
    assert p.events[0].has_valid_outcome


def test_multi_event():
    p = PremisEvents(multi_premis_event)
    assert len(p.events) == 3
    assert p.events[0].event_id == "222"
    assert p.events[0].event_detail == "Ionic Defibulizer Plus"
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "EXPORT"
    assert p.events[0].event_outcome == "OK"
    assert p.events[0].event_datetime == "2020-03-30T05:28:40Z"
    assert not p.events[0].is_valid
    assert p.events[0].has_valid_outcome
    assert p.events[1].event_id == "333"
    assert p.events[1].event_detail == "Ionic Defibulizer"
    assert p.events[1].fragment_id == "d4e5f6"
    assert p.events[1].event_type == "FLOW.ARCHIVED"
    assert p.events[1].event_outcome == "OK"
    assert p.events[1].event_datetime == "2019-03-30T05:28:40Z"
    assert not p.events[1].is_valid
    assert p.events[1].has_valid_outcome
    assert p.events[2].event_id == "444"
    assert p.events[2].event_detail == "Ionic Defibulizer 2"
    assert p.events[2].fragment_id == "g7h8j9"
    assert p.events[2].event_type == "RECORDS.FLOW.ARCHIVED"
    assert p.events[2].event_outcome == "OK"
    assert p.events[2].event_datetime == "2019-03-30T05:28:40Z"
    assert p.events[2].is_valid
    assert p.events[2].has_valid_outcome

def test_invalid_premis_event():
    with pytest.raises(InvalidPremisEventException) as e:
        p = PremisEvents(invalid_premis_event)

def test_invalid_xml_event():
    with pytest.raises(XMLSyntaxError) as e:
        p = PremisEvents(invalid_xml_event)

def test_single_event_no_external_id():
    p = PremisEvents(single_event_no_external_id)
    assert p.events[0].external_id == ""

def test_get_xpath_from_event():
    input_xml = "<xml><path>value</path></xml>"
    tree = parse_xml_string(input_xml)
    p = PremisEvent(tree)
    assert p._get_xpath_from_event("no_such_path") == ""
    assert p._get_xpath_from_event("path") == "value"
