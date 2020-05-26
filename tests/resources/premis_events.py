#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

folder = os.path.join(os.getcwd(), 'tests', 'resources')

with open(os.path.join(folder, 'single_premis_event.xml'), 'rb') as f:
    single_premis_event = f.read()

with open(os.path.join(folder, 'multi_premis_event.xml'), 'rb') as f:
    multi_premis_event = f.read()

with open(os.path.join(folder, 'invalid_premis_event.xml'), 'rb') as f:
    invalid_premis_event = f.read()

with open(os.path.join(folder, 'invalid_xml_event.xml'), 'rb') as f:
    invalid_xml_event = f.read()

with open(os.path.join(folder, 'single_event_no_external_id.xml'), 'rb') as f:
    single_event_no_external_id = f.read()
