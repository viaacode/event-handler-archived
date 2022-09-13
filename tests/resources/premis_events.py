#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

folder = os.path.join(os.getcwd(), 'tests', 'resources')

def _load_resource(filename):
    with open(os.path.join(folder, filename), 'rb') as f:
        contents = f.read()
    return contents

single_premis_event = _load_resource('single_premis_event.xml')
single_premis_event_nok = _load_resource('single_premis_event_nok.xml')
multi_premis_event = _load_resource('multi_premis_event.xml')
invalid_premis_event = _load_resource('invalid_premis_event.xml')
invalid_xml_event = _load_resource('invalid_xml_event.xml')
single_event_no_external_id = _load_resource('single_event_no_external_id.xml')
single_premis_event_archived_on_tape = _load_resource('single_premis_event_archived_on_tape.xml')
single_premis_event_archived_flow = _load_resource('single_premis_event_archived_flow.xml')
