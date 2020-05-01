#!/usr/bin/env python3
# -*- coding: utf-8 -*-


with open('./tests/resources/single_premis_event.xml', 'rb') as f:
    single_premis_event = f.read()

with open('./tests/resources/multi_premis_event.xml', 'rb') as f:
    multi_premis_event = f.read()

with open('./tests/resources/invalid_premis_event.xml', 'rb') as f:
    invalid_premis_event = f.read()

with open('./tests/resources/invalid_xml_event.xml', 'rb') as f:
    invalid_xml_event = f.read()
