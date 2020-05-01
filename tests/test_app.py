#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO

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
    schema = etree.XMLSchema(file="./tests/resources/essenceArchivedEvent.xsd")
    parser = etree.XMLParser(schema = schema)
    # Act & Assert: parsing with a schema-aware parser will raise an
    # `lxml.etree.XMLSyntaxError` if not valid
    tree = etree.parse(BytesIO(xml.encode('utf-8')), parser)
