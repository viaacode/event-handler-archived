#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree

# Constants
PREMIS_NAMESPACE = "info:lc/xmlns/premis-v2"


class PremisEvent:
    """Convenience class for a single XML Premis Event"""

    def __init__(self, element):
        self.xml_element = element
        self.event_type: str = self._get_event_type()
        self.fragment_id: str = self._get_fragment_id()

    def _get_event_type(self) -> str:
        return self.xml_element.xpath(
            "./p:eventType", namespaces={"p": PREMIS_NAMESPACE}
        )[0].text

    def _get_fragment_id(self) -> str:
        return self.xml_element.xpath(
            "./p:linkingObjectIdentifier[p:linkingObjectIdentifierType='MEDIAHAVEN_ID']/p:linkingObjectIdentifierValue",
            namespaces={"p": PREMIS_NAMESPACE},
        )[0].text

    def to_string(self, pretty=False) -> str:
        return etree.tostring(events[0], pretty_print=pretty).decode("utf-8")


class PremisEvents:
    """Convenience class for XML Premis Events"""

    def __init__(self, input_xml):
        self.input_xml = input_xml
        self.xml_tree = self._xml_to_tree(input_xml)
        self.docinfo = self.xml_tree.docinfo
        self.events = self._parse_events()

    def _xml_to_tree(self, input_xml):
        """Parse the input XML to a DOM"""
        tree = etree.parse(BytesIO(input_xml))
        return tree

    def _parse_events(self):
        """Parse possibly multiple events in the XML-DOM and return a list of
        DOM Premis-events"""
        events = []
        elements = self.xml_tree.xpath(
            "/events/p:event", namespaces={"p": PREMIS_NAMESPACE}
        )
        for element in elements:
            events.append(PremisEvent(element))
        return events
