#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
import os

from lxml import etree

from app.app import (
    generate_vrt_xml
)


def test_generate_vrt_xml():
    # Arrange
    pid = 'a1b2c3'
    object_key = 'an_object_key'
    md5 = 'abcdef123456'
    bucket = 'a_bucket'
    # Act
    xml = generate_vrt_xml(pid, md5, bucket, object_key)
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    # Assert
    ns = {"m":"http://www.vrt.be/mig/viaa/api"}
    assert tree.xpath('/m:essenceArchivedEvent/m:pid/text()', namespaces=ns)[0] == pid
    assert tree.xpath('/m:essenceArchivedEvent/m:file/text()', namespaces=ns)[0] == object_key
    assert tree.xpath('/m:essenceArchivedEvent/m:s3bucket/text()', namespaces=ns)[0] == bucket
    assert tree.xpath('/m:essenceArchivedEvent/m:md5sum/text()', namespaces=ns)[0] == md5

def test_generate_vrt_xml_against_xsd():
    # Arrange
    pid = 'a1b2c3'
    object_key = 'an_object_key'
    md5 = 'abcdef123456'
    bucket = 'a_bucket'
    xml = generate_vrt_xml(pid, md5, bucket, object_key)
    xsd_file = os.path.join(os.path.dirname(__file__),'resources','essenceArchivedEvent.xsd')
    schema = etree.XMLSchema(file=xsd_file)
    # Act
    tree = etree.parse(BytesIO(xml.encode('utf-8')))
    is_xml_valid = schema.validate(tree)
    # Assert
    assert is_xml_valid == True
