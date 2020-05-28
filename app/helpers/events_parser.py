#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree

# Constants
PREMIS_NAMESPACE = "info:lc/xmlns/premis-v2"
VALID_EVENT_TYPES = ["FLOW.ARCHIVED", "RECORDS.FLOW.ARCHIVED"]


class InvalidPremisEventException(Exception):
    """Valid XML but not a Premis event"""

    pass


class PremisEvent:
    """Convenience class for a single XML Premis Event"""

    XPATHS = {
        "event_type": "./p:eventType",
        "event_datetime":"./p:eventDateTime",
        "event_detail": "./p:eventDetail",
        "event_id": "./p:eventIdentifier[p:eventIdentifierType='MEDIAHAVEN_EVENT']/p:eventIdentifierValue",
        "event_outcome": "./p:eventOutcomeInformation/p:eventOutcome",
        "fragment_id": "./p:linkingObjectIdentifier[p:linkingObjectIdentifierType='MEDIAHAVEN_ID']/p:linkingObjectIdentifierValue",
        "external_id": "./p:linkingObjectIdentifier[p:linkingObjectIdentifierType='EXTERNAL_ID']/p:linkingObjectIdentifierValue",
    }

    def __init__(self, element):
        self.xml_element = element
        self.event_type: str = self._get_xpath_from_event(self.XPATHS["event_type"])
        self.event_datetime: str = self._get_xpath_from_event(self.XPATHS["event_datetime"])
        self.event_detail: str = self._get_xpath_from_event(self.XPATHS["event_detail"])
        self.event_id: str = self._get_xpath_from_event(self.XPATHS["event_id"])
        self.event_outcome: str = self._get_xpath_from_event(self.XPATHS["event_outcome"])
        self.fragment_id: str = self._get_xpath_from_event(self.XPATHS["fragment_id"])
        self.external_id: str = self._get_xpath_from_event(self.XPATHS["external_id"])
        self.is_valid: bool = self._is_valid()

    def _get_xpath_from_event(self, xpath) -> str:
        """Parses based on an xpath, returns empty string if absent"""
        try:
            return self.xml_element.xpath(
                xpath, namespaces={"p": PREMIS_NAMESPACE}
            )[0].text
        except IndexError:
            return ""

    def _is_valid(self):
        """A PremisEvent is valid only if:
            - it has a valid eventType for this particular application,
            - if it has a fragment ID.
        """
        if (self.event_type in VALID_EVENT_TYPES and
            self.fragment_id):
            return True
        return False


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
        if not events:
            raise InvalidPremisEventException(
                f'No events found at xpath "/events/p:event": Root tag=<{self.xml_tree.docinfo.root_name}>, encoding="{self.xml_tree.docinfo.encoding}"'
            )
        return events
