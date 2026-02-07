"""
HL7 Message Parser Service

This module provides HL7v2 message parsing and conversion to FHIR resources
for integration with legacy healthcare systems.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from common.utils.logging import get_logger

logger = get_logger(__name__)


class HL7MessageType(str, Enum):
    """HL7 message types."""
    ADT = "ADT"  # Admit, Discharge, Transfer
    ORU = "ORU"  # Observation Result
    ORM = "ORM"  # Order Message
    SIU = "SIU"  # Scheduling Information
    DFT = "DFT"  # Detailed Financial Transaction
    MDM = "MDM"  # Medical Document Management
    QRY = "QRY"  # Query
    RSP = "RSP"  # Response


class HL7SegmentType(str, Enum):
    """HL7 segment types."""
    MSH = "MSH"  # Message Header
    PID = "PID"  # Patient Identification
    PV1 = "PV1"  # Patient Visit
    ORC = "ORC"  # Common Order
    OBR = "OBR"  # Observation Request
    OBX = "OBX"  # Observation Result
    NTE = "NTE"  # Notes and Comments
    DG1 = "DG1"  # Diagnosis
    PR1 = "PR1"  # Procedures
    RXO = "RXO"  # Pharmacy Order
    RXA = "RXA"  # Pharmacy Administration


@dataclass
class HL7Field:
    """HL7 field representation."""
    value: str
    components: List[str]
    subcomponents: List[List[str]]


@dataclass
class HL7Segment:
    """HL7 segment representation."""
    segment_type: str
    fields: List[HL7Field]


class HL7Message(BaseModel):
    """HL7 message model."""
    message_type: HL7MessageType
    trigger_event: str
    message_control_id: str
    processing_id: str
    version_id: str
    sequence_number: Optional[int] = None
    segments: List[HL7Segment] = Field(default_factory=list)
    raw_message: str = ""
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class HL7ParsingError(Exception):
    """HL7 parsing error."""
    pass


class HL7ValidationError(Exception):
    """HL7 validation error."""
    pass


class HL7Parser:
    """HL7 message parser."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_separator = "|"
        self.component_separator = "^"
        self.subcomponent_separator = "&"
        self.repetition_separator = "~"
        self.escape_character = "\\"
    
    def parse_message(self, raw_message: str) -> HL7Message:
        """Parse a raw HL7 message."""
        try:
            # Clean the message
            raw_message = raw_message.strip()
            if not raw_message:
                raise HL7ParsingError("Empty message")
            
            # Split into segments
            segments = []
            for line in raw_message.split('\r'):
                line = line.strip()
                if line:
                    segment = self._parse_segment(line)
                    segments.append(segment)
            
            if not segments:
                raise HL7ParsingError("No segments found in message")
            
            # Parse MSH segment for message header
            msh_segment = segments[0]
            if msh_segment.segment_type != "MSH":
                raise HL7ParsingError("Message must start with MSH segment")
            
            # Extract message header information
            message_type = self._extract_message_type(msh_segment)
            trigger_event = self._extract_trigger_event(msh_segment)
            message_control_id = self._get_field_value(msh_segment, 10)
            processing_id = self._get_field_value(msh_segment, 11)
            version_id = self._get_field_value(msh_segment, 12)
            
            return HL7Message(
                message_type=message_type,
                trigger_event=trigger_event,
                message_control_id=message_control_id,
                processing_id=processing_id,
                version_id=version_id,
                segments=segments,
                raw_message=raw_message
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing HL7 message: {e}")
            raise HL7ParsingError(f"Failed to parse HL7 message: {str(e)}")
    
    def _parse_segment(self, segment_line: str) -> HL7Segment:
        """Parse a single HL7 segment."""
        try:
            # Split by field separator
            fields = segment_line.split(self.field_separator)
            
            if len(fields) < 2:
                raise HL7ParsingError(f"Invalid segment format: {segment_line}")
            
            segment_type = fields[0]
            parsed_fields = []
            
            # Parse each field
            for field_value in fields[1:]:
                field = self._parse_field(field_value)
                parsed_fields.append(field)
            
            return HL7Segment(
                segment_type=segment_type,
                fields=parsed_fields
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing segment: {e}")
            raise HL7ParsingError(f"Failed to parse segment: {str(e)}")
    
    def _parse_field(self, field_value: str) -> HL7Field:
        """Parse a single HL7 field."""
        try:
            # Handle empty field
            if not field_value:
                return HL7Field(value="", components=[], subcomponents=[])
            
            # Split by component separator
            components = field_value.split(self.component_separator)
            
            # Parse subcomponents for each component
            subcomponents = []
            for component in components:
                if self.subcomponent_separator in component:
                    subcomps = component.split(self.subcomponent_separator)
                    subcomponents.append(subcomps)
                else:
                    subcomponents.append([component])
            
            return HL7Field(
                value=field_value,
                components=components,
                subcomponents=subcomponents
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing field: {e}")
            raise HL7ParsingError(f"Failed to parse field: {str(e)}")
    
    def _extract_message_type(self, msh_segment: HL7Segment) -> HL7MessageType:
        """Extract message type from MSH segment."""
        try:
            message_type_str = self._get_field_value(msh_segment, 9)
            if not message_type_str:
                raise HL7ParsingError("Message type not found in MSH-9")
            
            # Extract the message type (first component)
            if "^" in message_type_str:
                message_type_str = message_type_str.split("^")[0]
            
            return HL7MessageType(message_type_str)
            
        except Exception as e:
            self.logger.error(f"Error extracting message type: {e}")
            raise HL7ParsingError(f"Failed to extract message type: {str(e)}")
    
    def _extract_trigger_event(self, msh_segment: HL7Segment) -> str:
        """Extract trigger event from MSH segment."""
        try:
            message_type_str = self._get_field_value(msh_segment, 9)
            if not message_type_str:
                return ""
            
            # Extract trigger event (second component)
            if "^" in message_type_str:
                parts = message_type_str.split("^")
                if len(parts) > 1:
                    return parts[1]
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting trigger event: {e}")
            return ""
    
    def _get_field_value(self, segment: HL7Segment, field_index: int) -> str:
        """Get field value by index (1-based)."""
        try:
            if field_index <= 0 or field_index > len(segment.fields):
                return ""
            
            field = segment.fields[field_index - 1]
            return field.value
            
        except Exception as e:
            self.logger.error(f"Error getting field value: {e}")
            return ""
    
    def _get_component_value(self, segment: HL7Segment, field_index: int, component_index: int) -> str:
        """Get component value by field and component index (1-based)."""
        try:
            if field_index <= 0 or field_index > len(segment.fields):
                return ""
            
            field = segment.fields[field_index - 1]
            if component_index <= 0 or component_index > len(field.components):
                return ""
            
            return field.components[component_index - 1]
            
        except Exception as e:
            self.logger.error(f"Error getting component value: {e}")
            return ""


class HL7ToFHIRConverter:
    """Convert HL7 messages to FHIR resources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = HL7Parser()
    
    def convert_message(self, hl7_message: HL7Message) -> Dict[str, Any]:
        """Convert HL7 message to FHIR resources."""
        try:
            if hl7_message.message_type == HL7MessageType.ORU:
                return self._convert_oru_message(hl7_message)
            elif hl7_message.message_type == HL7MessageType.ADT:
                return self._convert_adt_message(hl7_message)
            elif hl7_message.message_type == HL7MessageType.MDM:
                return self._convert_mdm_message(hl7_message)
            else:
                self.logger.warning(f"Unsupported message type: {hl7_message.message_type}")
                return {"error": f"Unsupported message type: {hl7_message.message_type}"}
                
        except Exception as e:
            self.logger.error(f"Error converting HL7 message: {e}")
            raise HL7ParsingError(f"Failed to convert HL7 message: {str(e)}")
    
    def _convert_oru_message(self, hl7_message: HL7Message) -> Dict[str, Any]:
        """Convert ORU (Observation Result) message to FHIR resources."""
        try:
            resources = []
            
            # Extract patient information
            patient_info = self._extract_patient_info(hl7_message)
            
            # Extract observations
            observations = self._extract_observations(hl7_message)
            
            # Create FHIR Patient resource
            if patient_info:
                patient_resource = {
                    "resourceType": "Patient",
                    "id": patient_info.get("id"),
                    "identifier": [
                        {
                            "system": "http://hospital.example.com/patients",
                            "value": patient_info.get("id")
                        }
                    ],
                    "name": [
                        {
                            "family": patient_info.get("last_name", ""),
                            "given": [patient_info.get("first_name", "")]
                        }
                    ],
                    "gender": patient_info.get("gender", "unknown"),
                    "birthDate": patient_info.get("birth_date")
                }
                resources.append(patient_resource)
            
            # Create FHIR Observation resources
            for obs in observations:
                observation_resource = {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "laboratory",
                                    "display": "Laboratory"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": obs.get("loinc_code", ""),
                                "display": obs.get("test_name", "")
                            }
                        ],
                        "text": obs.get("test_name", "")
                    },
                    "subject": {
                        "reference": f"Patient/{patient_info.get('id')}"
                    },
                    "effectiveDateTime": obs.get("effective_date"),
                    "issued": obs.get("issued_date"),
                    "valueQuantity": {
                        "value": obs.get("value"),
                        "unit": obs.get("unit"),
                        "system": "http://unitsofmeasure.org",
                        "code": obs.get("unit_code", "")
                    },
                    "referenceRange": [
                        {
                            "low": {
                                "value": obs.get("reference_range_low"),
                                "unit": obs.get("unit")
                            },
                            "high": {
                                "value": obs.get("reference_range_high"),
                                "unit": obs.get("unit")
                            }
                        }
                    ] if obs.get("reference_range_low") or obs.get("reference_range_high") else []
                }
                resources.append(observation_resource)
            
            return {
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [
                    {
                        "resource": resource
                    } for resource in resources
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error converting ORU message: {e}")
            raise
    
    def _extract_patient_info(self, hl7_message: HL7Message) -> Dict[str, Any]:
        """Extract patient information from HL7 message."""
        try:
            for segment in hl7_message.segments:
                if segment.segment_type == "PID":
                    return {
                        "id": self.parser._get_component_value(segment, 3, 1),
                        "first_name": self.parser._get_component_value(segment, 5, 2),
                        "last_name": self.parser._get_component_value(segment, 5, 1),
                        "gender": self.parser._get_field_value(segment, 8),
                        "birth_date": self.parser._get_field_value(segment, 7)
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error extracting patient info: {e}")
            return {}
    
    def _extract_observations(self, hl7_message: HL7Message) -> List[Dict[str, Any]]:
        """Extract observations from HL7 message."""
        try:
            observations = []
            
            for segment in hl7_message.segments:
                if segment.segment_type == "OBX":
                    observation = {
                        "test_name": self.parser._get_component_value(segment, 3, 2),
                        "loinc_code": self.parser._get_component_value(segment, 3, 1),
                        "value": self.parser._get_field_value(segment, 5),
                        "unit": self.parser._get_component_value(segment, 6, 2),
                        "unit_code": self.parser._get_component_value(segment, 6, 1),
                        "reference_range_low": self.parser._get_component_value(segment, 7, 1),
                        "reference_range_high": self.parser._get_component_value(segment, 7, 2),
                        "effective_date": self.parser._get_field_value(segment, 14),
                        "issued_date": self.parser._get_field_value(segment, 19)
                    }
                    observations.append(observation)
            
            return observations
            
        except Exception as e:
            self.logger.error(f"Error extracting observations: {e}")
            return []
    
    def _convert_adt_message(self, hl7_message: HL7Message) -> Dict[str, Any]:
        """Convert ADT (Admit, Discharge, Transfer) message to FHIR resources."""
        # TODO: Implement ADT message conversion
        return {"error": "ADT conversion not yet implemented"}
    
    def _convert_mdm_message(self, hl7_message: HL7Message) -> Dict[str, Any]:
        """Convert MDM (Medical Document Management) message to FHIR resources."""
        # TODO: Implement MDM message conversion
        return {"error": "MDM conversion not yet implemented"}


# Global instances
hl7_parser = HL7Parser()
hl7_converter = HL7ToFHIRConverter() 