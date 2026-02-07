"""
Imaging Analyzer Agent
Analyzes medical imaging reports for abnormalities, findings, and clinical significance.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload

from .base_agent import BaseMedicalAgent, AgentResult
# from ..models.imaging_reports_db import ImagingReportDB  # Commented out for testing
from ..utils.event_streaming import MedicalRecordsEventProducer


class ImagingModality(str, Enum):
    """Types of medical imaging modalities."""
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    PET = "pet"
    NUCLEAR_MEDICINE = "nuclear_medicine"
    FLUOROSCOPY = "fluoroscopy"
    MAMMOGRAM = "mammogram"
    DEXA = "dexa"
    OTHER = "other"


class FindingSeverity(str, Enum):
    """Severity levels for imaging findings."""
    NORMAL = "normal"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class BodyRegion(str, Enum):
    """Body regions for imaging studies."""
    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    SPINE = "spine"
    EXTREMITIES = "extremities"
    CARDIOVASCULAR = "cardiovascular"
    OTHER = "other"


@dataclass
class ImagingFinding:
    """Individual imaging finding."""
    finding_type: str
    location: str
    description: str
    severity: FindingSeverity
    measurements: Optional[Dict[str, float]]
    clinical_significance: str
    differential_diagnosis: List[str]
    recommended_follow_up: str


@dataclass
class ImagingAnalysis:
    """Complete imaging analysis."""
    patient_id: UUID
    report_id: UUID
    analysis_date: datetime
    modality: ImagingModality
    body_region: BodyRegion
    findings: List[ImagingFinding]
    normal_findings: List[str]
    abnormal_findings: List[ImagingFinding]
    critical_findings: List[ImagingFinding]
    impression: str
    recommendations: List[str]
    follow_up_imaging: List[str]
    clinical_correlation: str
    overall_assessment: str


class ImagingAnalyzerAgent(BaseMedicalAgent):
    """Agent for analyzing medical imaging reports."""
    
    def __init__(self):
        super().__init__("ImagingAnalyzerAgent")
        self.event_producer = MedicalRecordsEventProducer()
        
        # Imaging modality patterns
        self.modality_patterns = {
            ImagingModality.XRAY: [
                r'\b(x.?ray|xray|radiograph|chest x.?ray|abdominal x.?ray|bone x.?ray)\b',
                r'\b(chest radiograph|abdominal radiograph|bone radiograph)\b'
            ],
            ImagingModality.CT: [
                r'\b(ct|cat scan|computed tomography|ct scan)\b',
                r'\b(chest ct|abdominal ct|head ct|brain ct|spine ct)\b'
            ],
            ImagingModality.MRI: [
                r'\b(mri|magnetic resonance|magnetic resonance imaging)\b',
                r'\b(brain mri|spine mri|knee mri|shoulder mri|cardiac mri)\b'
            ],
            ImagingModality.ULTRASOUND: [
                r'\b(ultrasound|sonogram|echo|echocardiogram|us)\b',
                r'\b(abdominal ultrasound|pelvic ultrasound|cardiac echo)\b'
            ],
            ImagingModality.PET: [
                r'\b(pet|positron emission tomography|pet scan)\b',
                r'\b(pet.?ct|pet.?mri|f18.?fdg)\b'
            ],
            ImagingModality.MAMMOGRAM: [
                r'\b(mammogram|mammography|breast imaging)\b',
                r'\b(screening mammogram|diagnostic mammogram)\b'
            ]
        }
        
        # Body region patterns
        self.region_patterns = {
            BodyRegion.HEAD: [
                r'\b(head|brain|skull|intracranial|intracerebral)\b',
                r'\b(cerebral|cranial|encephalic|brainstem|cerebellum)\b'
            ],
            BodyRegion.CHEST: [
                r'\b(chest|thorax|thoracic|lung|pulmonary|cardiac|heart)\b',
                r'\b(mediastinum|pleura|bronchi|trachea|esophagus)\b'
            ],
            BodyRegion.ABDOMEN: [
                r'\b(abdomen|abdominal|liver|spleen|kidney|pancreas)\b',
                r'\b(stomach|intestine|colon|gallbladder|adrenal)\b'
            ],
            BodyRegion.SPINE: [
                r'\b(spine|spinal|vertebra|vertebral|cervical|thoracic|lumbar)\b',
                r'\b(sacral|coccyx|intervertebral|spinal canal)\b'
            ],
            BodyRegion.EXTREMITIES: [
                r'\b(extremity|extremities|arm|leg|hand|foot|shoulder|hip)\b',
                r'\b(knee|elbow|wrist|ankle|joint|bone|muscle|tendon)\b'
            ]
        }
        
        # Critical finding patterns
        self.critical_patterns = [
            r'\b(mass|tumor|neoplasm|cancer|carcinoma|malignancy)\b',
            r'\b(hemorrhage|bleeding|hematoma|subdural|epidural)\b',
            r'\b(pneumothorax|pneumonia|pulmonary embolism|pe)\b',
            r'\b(aortic dissection|aneurysm|rupture)\b',
            r'\b(fracture|dislocation|spinal cord injury)\b',
            r'\b(obstruction|perforation|ischemia|infarction)\b'
        ]
        
        # Normal finding patterns
        self.normal_patterns = [
            r'\b(normal|unremarkable|no acute|no significant)\b',
            r'\b(within normal limits|wnl|no abnormality)\b',
            r'\b(no evidence of|no signs of|no findings of)\b'
        ]
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Analyze medical imaging report for findings and clinical significance.
        
        Args:
            data: Dictionary containing imaging report information
            db: Database session
            
        Returns:
            AgentResult: Analysis result with findings, impressions, and recommendations
        """
        patient_id = data.get("patient_id")
        report_id = data.get("report_id")
        report_text = data.get("report_text")
        
        if not patient_id:
            return AgentResult(
                success=False,
                error="patient_id is required"
            )
        
        if not report_text:
            return AgentResult(
                success=False,
                error="report_text is required"
            )
        
        try:
            # Determine imaging modality
            modality = self._identify_modality(report_text)
            
            # Determine body region
            body_region = self._identify_body_region(report_text)
            
            # Extract findings
            findings = await self._extract_findings(report_text, modality)
            
            # Separate normal and abnormal findings
            normal_findings = [f for f in findings if f.severity == FindingSeverity.NORMAL]
            abnormal_findings = [f for f in findings if f.severity != FindingSeverity.NORMAL]
            critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
            
            # Generate impression
            impression = self._generate_impression(findings, modality, body_region)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(findings, modality)
            
            # Suggest follow-up imaging
            follow_up_imaging = self._suggest_follow_up_imaging(findings, modality, body_region)
            
            # Generate clinical correlation
            clinical_correlation = self._generate_clinical_correlation(findings, modality, body_region)
            
            # Overall assessment
            overall_assessment = self._generate_overall_assessment(findings, critical_findings)
            
            # Create analysis summary
            analysis = ImagingAnalysis(
                patient_id=UUID(patient_id),
                report_id=UUID(report_id) if report_id else UUID('00000000-0000-0000-0000-000000000000'),
                analysis_date=datetime.utcnow(),
                modality=modality,
                body_region=body_region,
                findings=findings,
                normal_findings=[f.description for f in normal_findings],
                abnormal_findings=abnormal_findings,
                critical_findings=critical_findings,
                impression=impression,
                recommendations=recommendations,
                follow_up_imaging=follow_up_imaging,
                clinical_correlation=clinical_correlation,
                overall_assessment=overall_assessment
            )
            
            # Update imaging report with analysis
            if report_id:
                await self._update_imaging_report_analysis(db, report_id, analysis)
            
            # Publish analysis event to Kafka
            await self._publish_imaging_analysis_event(analysis)
            
            # Generate insights
            insights = self._generate_insights(analysis)
            
            return AgentResult(
                success=True,
                data={
                    "patient_id": str(patient_id),
                    "report_id": str(analysis.report_id),
                    "analysis_date": analysis.analysis_date.isoformat(),
                    "modality": modality.value,
                    "body_region": body_region.value,
                    "findings_count": len(findings),
                    "normal_findings_count": len(normal_findings),
                    "abnormal_findings_count": len(abnormal_findings),
                    "critical_findings_count": len(critical_findings),
                    "findings": [self._finding_to_dict(f) for f in findings],
                    "impression": impression,
                    "recommendations": recommendations,
                    "follow_up_imaging": follow_up_imaging,
                    "clinical_correlation": clinical_correlation,
                    "overall_assessment": overall_assessment
                },
                insights=insights,
                recommendations=recommendations,
                confidence=0.88
            )
            
        except Exception as e:
            self.logger.error(f"Imaging analysis failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Imaging analysis failed: {str(e)}"
            )
    
    def _identify_modality(self, report_text: str) -> ImagingModality:
        """Identify imaging modality from report text."""
        text_lower = report_text.lower()
        
        for modality, patterns in self.modality_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return modality
        
        return ImagingModality.OTHER
    
    def _identify_body_region(self, report_text: str) -> BodyRegion:
        """Identify body region from report text."""
        text_lower = report_text.lower()
        
        for region, patterns in self.region_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return region
        
        return BodyRegion.OTHER
    
    async def _extract_findings(self, report_text: str, modality: ImagingModality) -> List[ImagingFinding]:
        """Extract findings from imaging report."""
        findings = []
        
        # Split report into sections
        sections = self._parse_report_sections(report_text)
        
        # Extract findings from each section
        for section_name, section_text in sections.items():
            section_findings = self._extract_section_findings(section_text, section_name, modality)
            findings.extend(section_findings)
        
        # If no structured findings, extract from full text
        if not findings:
            findings = self._extract_general_findings(report_text, modality)
        
        return findings
    
    def _parse_report_sections(self, report_text: str) -> Dict[str, str]:
        """Parse imaging report into sections."""
        sections = {}
        
        # Common section headers
        section_headers = [
            "technique", "technique:", "technique description",
            "findings", "findings:", "impression", "impression:",
            "conclusion", "conclusion:", "diagnosis", "diagnosis:",
            "comparison", "comparison:", "history", "history:"
        ]
        
        lines = report_text.split('\n')
        current_section = "general"
        current_text = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line is a section header
            is_header = any(header in line_lower for header in section_headers)
            
            if is_header and current_text:
                sections[current_section] = '\n'.join(current_text)
                current_section = line_lower.replace(':', '').strip()
                current_text = []
            else:
                current_text.append(line)
        
        # Add final section
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        return sections
    
    def _extract_section_findings(self, section_text: str, section_name: str, modality: ImagingModality) -> List[ImagingFinding]:
        """Extract findings from a specific section."""
        findings = []
        
        # Skip technique sections
        if "technique" in section_name.lower():
            return findings
        
        # Extract sentences that might contain findings
        sentences = re.split(r'[.!?]+', section_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Check for normal findings
            if self._is_normal_finding(sentence):
                findings.append(ImagingFinding(
                    finding_type="normal",
                    location="general",
                    description=sentence,
                    severity=FindingSeverity.NORMAL,
                    measurements=None,
                    clinical_significance="Normal finding",
                    differential_diagnosis=[],
                    recommended_follow_up="None required"
                ))
                continue
            
            # Check for abnormal findings
            if self._is_abnormal_finding(sentence):
                finding = self._parse_abnormal_finding(sentence, modality)
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _extract_general_findings(self, report_text: str, modality: ImagingModality) -> List[ImagingFinding]:
        """Extract findings from full report text when structured parsing fails."""
        findings = []
        
        # Check for normal report
        if self._is_normal_report(report_text):
            findings.append(ImagingFinding(
                finding_type="normal",
                location="general",
                description="Normal imaging study",
                severity=FindingSeverity.NORMAL,
                measurements=None,
                clinical_significance="Normal imaging study",
                differential_diagnosis=[],
                recommended_follow_up="None required"
            ))
            return findings
        
        # Extract abnormal findings
        sentences = re.split(r'[.!?]+', report_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            if self._is_abnormal_finding(sentence):
                finding = self._parse_abnormal_finding(sentence, modality)
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _is_normal_finding(self, text: str) -> bool:
        """Check if text describes a normal finding."""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.normal_patterns)
    
    def _is_normal_report(self, text: str) -> bool:
        """Check if the entire report is normal."""
        text_lower = text.lower()
        normal_indicators = [
            "normal study",
            "unremarkable",
            "no acute abnormality",
            "no significant finding",
            "within normal limits"
        ]
        return any(indicator in text_lower for indicator in normal_indicators)
    
    def _is_abnormal_finding(self, text: str) -> bool:
        """Check if text describes an abnormal finding."""
        text_lower = text.lower()
        
        # Skip normal findings
        if self._is_normal_finding(text):
            return False
        
        # Look for abnormal indicators
        abnormal_indicators = [
            "abnormal", "abnormality", "lesion", "mass", "nodule",
            "opacity", "density", "effusion", "edema", "inflammation",
            "fracture", "dislocation", "herniation", "stenosis",
            "dilation", "enlargement", "atrophy", "degeneration"
        ]
        
        return any(indicator in text_lower for indicator in abnormal_indicators)
    
    def _parse_abnormal_finding(self, text: str, modality: ImagingModality) -> Optional[ImagingFinding]:
        """Parse an abnormal finding from text."""
        try:
            # Determine severity
            severity = self._determine_finding_severity(text)
            
            # Extract location
            location = self._extract_location(text)
            
            # Extract measurements if present
            measurements = self._extract_measurements(text)
            
            # Generate clinical significance
            clinical_significance = self._generate_clinical_significance(text, severity, modality)
            
            # Generate differential diagnosis
            differential_diagnosis = self._generate_differential_diagnosis(text, modality)
            
            # Generate follow-up recommendation
            recommended_follow_up = self._generate_follow_up_recommendation(text, severity, modality)
            
            return ImagingFinding(
                finding_type=self._classify_finding_type(text),
                location=location,
                description=text,
                severity=severity,
                measurements=measurements,
                clinical_significance=clinical_significance,
                differential_diagnosis=differential_diagnosis,
                recommended_follow_up=recommended_follow_up
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing abnormal finding: {e}")
            return None
    
    def _determine_finding_severity(self, text: str) -> FindingSeverity:
        """Determine severity of a finding."""
        text_lower = text.lower()
        
        # Check for critical patterns
        for pattern in self.critical_patterns:
            if re.search(pattern, text_lower):
                return FindingSeverity.CRITICAL
        
        # Check for severity indicators
        if any(word in text_lower for word in ["severe", "critical", "acute", "emergency"]):
            return FindingSeverity.SEVERE
        elif any(word in text_lower for word in ["moderate", "significant", "marked"]):
            return FindingSeverity.MODERATE
        elif any(word in text_lower for word in ["mild", "minimal", "slight"]):
            return FindingSeverity.MILD
        else:
            return FindingSeverity.MODERATE  # Default to moderate
    
    def _extract_location(self, text: str) -> str:
        """Extract anatomical location from finding text."""
        # Common anatomical locations
        locations = [
            "right", "left", "bilateral", "anterior", "posterior",
            "superior", "inferior", "medial", "lateral", "central",
            "peripheral", "apical", "basal", "cortical", "subcortical"
        ]
        
        text_lower = text.lower()
        found_locations = [loc for loc in locations if loc in text_lower]
        
        if found_locations:
            return ", ".join(found_locations)
        else:
            return "unspecified"
    
    def _extract_measurements(self, text: str) -> Optional[Dict[str, float]]:
        """Extract measurements from finding text."""
        measurements = {}
        
        # Look for measurement patterns
        measurement_patterns = [
            r'(\d+(?:\.\d+)?)\s*(cm|mm|ml|cc)',
            r'(\d+(?:\.\d+)?)\s*(centimeter|millimeter|milliliter)',
            r'size[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm)',
            r'diameter[:\s]*(\d+(?:\.\d+)?)\s*(cm|mm)'
        ]
        
        for pattern in measurement_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    value = float(match[0])
                    unit = match[1]
                    measurements[f"size_{unit}"] = value
                except (ValueError, IndexError):
                    continue
        
        return measurements if measurements else None
    
    def _classify_finding_type(self, text: str) -> str:
        """Classify the type of finding."""
        text_lower = text.lower()
        
        finding_types = {
            "mass": ["mass", "tumor", "neoplasm", "lesion"],
            "nodule": ["nodule", "nodular"],
            "opacity": ["opacity", "density", "infiltrate"],
            "effusion": ["effusion", "fluid", "pleural", "pericardial"],
            "fracture": ["fracture", "break", "dislocation"],
            "degeneration": ["degeneration", "degenerative", "arthritis"],
            "inflammation": ["inflammation", "inflammatory", "edema"],
            "stenosis": ["stenosis", "narrowing", "obstruction"],
            "dilation": ["dilation", "enlargement", "ectasia"]
        }
        
        for finding_type, keywords in finding_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return finding_type
        
        return "abnormality"
    
    def _generate_clinical_significance(self, text: str, severity: FindingSeverity, modality: ImagingModality) -> str:
        """Generate clinical significance of a finding."""
        if severity == FindingSeverity.CRITICAL:
            return "Critical finding requiring immediate medical attention"
        elif severity == FindingSeverity.SEVERE:
            return "Severe abnormality requiring prompt evaluation"
        elif severity == FindingSeverity.MODERATE:
            return "Moderate abnormality requiring follow-up"
        else:
            return "Mild abnormality - monitor for changes"
    
    def _generate_differential_diagnosis(self, text: str, modality: ImagingModality) -> List[str]:
        """Generate differential diagnosis based on finding and modality."""
        text_lower = text.lower()
        differential = []
        
        # Add differentials based on finding type
        if "mass" in text_lower or "tumor" in text_lower:
            differential.extend(["Neoplasm", "Metastasis", "Benign tumor"])
        
        if "nodule" in text_lower:
            differential.extend(["Granuloma", "Infection", "Neoplasm"])
        
        if "effusion" in text_lower:
            differential.extend(["Infection", "Heart failure", "Malignancy"])
        
        if "fracture" in text_lower:
            differential.extend(["Trauma", "Osteoporosis", "Pathological fracture"])
        
        return differential[:3]  # Limit to top 3
    
    def _generate_follow_up_recommendation(self, text: str, severity: FindingSeverity, modality: ImagingModality) -> str:
        """Generate follow-up recommendation."""
        if severity == FindingSeverity.CRITICAL:
            return "Immediate medical evaluation required"
        elif severity == FindingSeverity.SEVERE:
            return "Urgent follow-up within 24-48 hours"
        elif severity == FindingSeverity.MODERATE:
            return "Follow-up imaging in 2-4 weeks"
        else:
            return "Routine follow-up as clinically indicated"
    
    def _generate_impression(self, findings: List[ImagingFinding], modality: ImagingModality, body_region: BodyRegion) -> str:
        """Generate overall impression from findings."""
        if not findings:
            return "No significant findings detected"
        
        critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        severe_findings = [f for f in findings if f.severity == FindingSeverity.SEVERE]
        
        if critical_findings:
            return f"Critical findings detected: {len(critical_findings)} critical abnormalities requiring immediate attention"
        elif severe_findings:
            return f"Significant abnormalities detected: {len(severe_findings)} severe findings requiring prompt evaluation"
        else:
            abnormal_count = len([f for f in findings if f.severity != FindingSeverity.NORMAL])
            return f"Mixed findings: {abnormal_count} abnormal findings with {len(findings) - abnormal_count} normal findings"
    
    def _generate_recommendations(self, findings: List[ImagingFinding], modality: ImagingModality) -> List[str]:
        """Generate clinical recommendations based on findings."""
        recommendations = []
        
        critical_findings = [f for f in findings if f.severity == FindingSeverity.CRITICAL]
        severe_findings = [f for f in findings if f.severity == FindingSeverity.SEVERE]
        
        if critical_findings:
            recommendations.append("Critical findings detected - immediate medical evaluation required")
        
        if severe_findings:
            recommendations.append("Severe abnormalities detected - urgent follow-up recommended")
        
        # Add modality-specific recommendations
        if modality == ImagingModality.CT:
            recommendations.append("Consider contrast-enhanced follow-up if clinically indicated")
        elif modality == ImagingModality.MRI:
            recommendations.append("Consider additional sequences if further characterization needed")
        
        if not recommendations:
            recommendations.append("Continue routine monitoring as clinically indicated")
        
        return recommendations
    
    def _suggest_follow_up_imaging(self, findings: List[ImagingFinding], modality: ImagingModality, body_region: BodyRegion) -> List[str]:
        """Suggest follow-up imaging studies."""
        follow_up = []
        
        # Add modality-specific follow-up
        if modality == ImagingModality.XRAY:
            if body_region == BodyRegion.CHEST:
                follow_up.append("Chest CT for further evaluation")
            elif body_region == BodyRegion.EXTREMITIES:
                follow_up.append("MRI for soft tissue evaluation")
        
        elif modality == ImagingModality.CT:
            if body_region == BodyRegion.HEAD:
                follow_up.append("Brain MRI for detailed evaluation")
            elif body_region == BodyRegion.CHEST:
                follow_up.append("PET-CT for metabolic evaluation")
        
        # Add finding-specific follow-up
        for finding in findings:
            if finding.severity in [FindingSeverity.CRITICAL, FindingSeverity.SEVERE]:
                if "mass" in finding.finding_type:
                    follow_up.append("Biopsy for tissue diagnosis")
                elif "nodule" in finding.finding_type:
                    follow_up.append("Follow-up imaging in 3-6 months")
        
        return list(set(follow_up))  # Remove duplicates
    
    def _generate_clinical_correlation(self, findings: List[ImagingFinding], modality: ImagingModality, body_region: BodyRegion) -> str:
        """Generate clinical correlation statement."""
        abnormal_count = len([f for f in findings if f.severity != FindingSeverity.NORMAL])
        
        if abnormal_count == 0:
            return "Imaging findings are within normal limits"
        elif abnormal_count == 1:
            return "Single abnormality detected - clinical correlation recommended"
        else:
            return f"Multiple abnormalities detected - comprehensive clinical evaluation recommended"
    
    def _generate_overall_assessment(self, findings: List[ImagingFinding], critical_findings: List[ImagingFinding]) -> str:
        """Generate overall assessment."""
        if critical_findings:
            return "CRITICAL - Immediate medical attention required"
        
        abnormal_count = len([f for f in findings if f.severity != FindingSeverity.NORMAL])
        
        if abnormal_count == 0:
            return "Normal imaging study"
        elif abnormal_count <= 2:
            return "Mild abnormalities - routine follow-up"
        else:
            return "Multiple abnormalities - comprehensive evaluation recommended"
    
    async def _update_imaging_report_analysis(self, db: AsyncSession, report_id: str, analysis: ImagingAnalysis):
        """Update imaging report with analysis metadata."""
        try:
            # This would update the imaging report with analysis metadata
            # Implementation depends on your database schema
            pass
        except Exception as e:
            self.logger.error(f"Error updating imaging report analysis: {e}")
    
    async def _publish_imaging_analysis_event(self, analysis: ImagingAnalysis):
        """Publish imaging analysis event to Kafka."""
        try:
            event = {
                "event_type": "imaging_analysis_completed",
                "timestamp": datetime.utcnow().isoformat(),
                "patient_id": str(analysis.patient_id),
                "report_id": str(analysis.report_id),
                "analysis_date": analysis.analysis_date.isoformat(),
                "modality": analysis.modality.value,
                "body_region": analysis.body_region.value,
                "findings_count": len(analysis.findings),
                "abnormal_findings_count": len(analysis.abnormal_findings),
                "critical_findings_count": len(analysis.critical_findings),
                "overall_assessment": analysis.overall_assessment,
                "source": "ImagingAnalyzerAgent"
            }
            
            await self.event_producer.publish_imaging_report_event(event)
            self.logger.info(f"📤 Published imaging analysis event for patient {analysis.patient_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing imaging analysis event: {e}")
    
    def _finding_to_dict(self, finding: ImagingFinding) -> Dict[str, Any]:
        """Convert ImagingFinding to dictionary."""
        return {
            "finding_type": finding.finding_type,
            "location": finding.location,
            "description": finding.description,
            "severity": finding.severity.value,
            "measurements": finding.measurements,
            "clinical_significance": finding.clinical_significance,
            "differential_diagnosis": finding.differential_diagnosis,
            "recommended_follow_up": finding.recommended_follow_up
        }
    
    def _generate_insights(self, analysis: ImagingAnalysis) -> List[str]:
        """Generate insights from imaging analysis."""
        insights = []
        
        insights.append(f"Analyzed {analysis.modality.value.upper()} imaging of {analysis.body_region.value}")
        insights.append(f"Detected {len(analysis.findings)} total findings")
        insights.append(f"Identified {len(analysis.abnormal_findings)} abnormal findings")
        
        if analysis.critical_findings:
            insights.append(f"Found {len(analysis.critical_findings)} critical findings requiring immediate attention")
        
        insights.append(f"Overall assessment: {analysis.overall_assessment}")
        
        return insights 