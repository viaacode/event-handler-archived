#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO

from lxml import etree

from tests.resources import single_premis_event
from app.app import (
    generate_vrt_xml
)


def test_generate_vrt_xml():
    pid = 'a1b2c3'
    object_key = 'an_object_key'
    xml = generate_vrt_xml(pid, object_key)
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    assert tree.xpath('/m:essenceArchivedEvent/m:pid/text()', namespaces={"m":"http://www.vrt.be/mig/viaa/api"})[0] == pid
    assert tree.xpath('/m:essenceArchivedEvent/m:file/text()', namespaces={"m":"http://www.vrt.be/mig/viaa/api"})[0] == object_key
