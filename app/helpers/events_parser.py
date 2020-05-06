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

    def __init__(self, element):
        self.xml_element = element
        self.event_type: str = self._get_event_type()
        self.event_datetime: str = self._get_event_datetime()
        self.event_detail: str = self._get_event_detail()
        self.event_id: str = self._get_event_id()
        self.event_outcome: str = self._get_event_outcome()
        self.fragment_id: str = self._get_fragment_id()
        self.external_id: str = self._get_external_id()
        self.is_valid: bool = self._is_valid()

    def _get_event_type(self) -> str:
        return self.xml_element.xpath(
            "./p:eventType", namespaces={"p": PREMIS_NAMESPACE}
        )[0].text

    def _get_event_datetime(self) -> str:
        return self.xml_element.xpath(
            "./p:eventDateTime", namespaces={"p": PREMIS_NAMESPACE}
        )[0].text

    def _get_event_detail(self) -> str:
        return self.xml_element.xpath(
            "./p:eventDetail", namespaces={"p": PREMIS_NAMESPACE}
        )[0].text

    def _get_event_id(self) -> str:
        return self.xml_element.xpath(
            "./p:eventIdentifier[p:eventIdentifierType='MEDIAHAVEN_EVENT']/p:eventIdentifierValue",
            namespaces={"p": PREMIS_NAMESPACE},
        )[0].text

    def _get_event_outcome(self) -> str:
        return self.xml_element.xpath(
            "./p:eventOutcomeInformation/p:eventOutcome",
            namespaces={"p": PREMIS_NAMESPACE},
        )[0].text

    def _get_fragment_id(self) -> str:
        return self.xml_element.xpath(
            "./p:linkingObjectIdentifier[p:linkingObjectIdentifierType='MEDIAHAVEN_ID']/p:linkingObjectIdentifierValue",
            namespaces={"p": PREMIS_NAMESPACE},
        )[0].text

    def _get_external_id(self) -> str:
        return self.xml_element.xpath(
            "./p:linkingObjectIdentifier[p:linkingObjectIdentifierType='EXTERNAL_ID']/p:linkingObjectIdentifierValue",
            namespaces={"p": PREMIS_NAMESPACE},
        )[0].text

    def _is_valid(self):
        """A PremisEvent is valid only if:
            - it has a valid eventType for this particular application,
            - if it has a fragment ID.
        """
        if (self.event_type in VALID_EVENT_TYPES and
            self.fragment_id):
            return True
        return False

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
        if not events:
            raise InvalidPremisEventException(
                f'No events found at xpath "/events/p:event": Root tag=<{self.xml_tree.docinfo.root_name}>, encoding="{self.xml_tree.docinfo.encoding}"'
            )
        return events
