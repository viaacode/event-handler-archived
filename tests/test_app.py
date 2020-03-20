#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tests.resources import single_premis_event
from app.app import get_event_and_fragment_id


def test_single_get_event_and_fragment_id():
    (event, fragment_id) = get_event_and_fragment_id(single_premis_event)
    assert event == "EXPORT"
    assert fragment_id == "a1b2c3"
