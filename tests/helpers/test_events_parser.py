#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from lxml.etree import XMLSyntaxError

from tests.resources import (
        single_premis_event,
        multi_premis_event,
        invalid_premis_event,
        invalid_xml_event,
)
from app.helpers.events_parser import (
    PremisEvents,
    InvalidPremisEventException,
)


def test_single_event():
    p = PremisEvents(single_premis_event)
    assert len(p.events) == 1
    #
    assert p.events[0].event_id == "111"
    assert p.events[0].event_detail == "Ionic Defibulizer"
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "FLOW.ARCHIVED"
    assert p.events[0].event_outcome == "NOK"
    assert p.events[0].is_valid

def test_multi_event():
    p = PremisEvents(multi_premis_event)
    assert len(p.events) == 2
    #
    assert p.events[0].event_id == "222"
    assert p.events[0].event_detail == "Ionic Defibulizer Plus"
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "EXPORT"
    assert p.events[0].event_outcome == "OK"
    assert not p.events[0].is_valid
    assert p.events[1].event_id == "333"
    assert p.events[1].event_detail == "Ionic Defibulizer"
    assert p.events[1].fragment_id == "d4e5f6"
    assert p.events[1].event_type == "FLOW.ARCHIVED"
    assert p.events[1].event_outcome == "OK"
    assert p.events[1].is_valid

def test_invalid_premis_event():
    with pytest.raises(InvalidPremisEventException) as e:
        p = PremisEvents(invalid_premis_event)

def test_invalid_xml_event():
    with pytest.raises(XMLSyntaxError) as e:
        p = PremisEvents(invalid_xml_event)
