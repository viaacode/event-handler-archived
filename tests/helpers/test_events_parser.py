#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tests.resources import single_premis_event, multi_premis_event
from app.helpers.events_parser import PremisEvents


def test_single_event():
    p = PremisEvents(single_premis_event)
    assert len(p.events) == 1
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "EXPORT"


def test_multi_event():
    p = PremisEvents(multi_premis_event)
    assert len(p.events) == 2
    assert p.events[0].fragment_id == "a1b2c3"
    assert p.events[0].event_type == "EXPORT"
    assert p.events[1].fragment_id == "d4e5f6"
    assert p.events[1].event_type == "FLOW.ARCHIVED"
