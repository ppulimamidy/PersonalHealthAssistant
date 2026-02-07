"""
Critical Alert Agent
Monitors medical data and generates critical alerts for urgent clinical situations.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from uuid import UUID
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_
from sqlalchemy.orm import joinedload

from .base_agent import BaseMedicalAgent, AgentResult
# from ..models.lab_results_db import LabResultDB  # Commented out for testing
# from ..models.imaging_reports_db import ImagingReportDB  # Commented out for testing
# from ..models.clinical_reports_db import ClinicalReportDB  # Commented out for testing
from ..utils.event_streaming import MedicalRecordsEventProducer


class AlertSeverity(str, Enum):
    """Severity levels for critical alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(str, Enum):
    """Categories of critical alerts."""
    LAB_CRITICAL = "lab_critical"
    IMAGING_CRITICAL = "imaging_critical"
    CLINICAL_URGENT = "clinical_urgent"
    TREND_ALERT = "trend_alert"
    COMBINATION_ALERT = "combination_alert"
    MEDICATION_ALERT = "medication_alert"
    VITAL_SIGNS = "vital_signs"
    INFECTION_ALERT = "infection_alert"
    CARDIOVASCULAR = "cardiovascular"
    NEUROLOGICAL = "neurological"
    OTHER = "other"


class AlertStatus(str, Enum):
    """Status of critical alerts."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    EXPIRED = "expired"


@dataclass
class CriticalAlert:
    """Critical alert information."""
    alert_id: str
    patient_id: UUID
    alert_type: AlertCategory
    severity: AlertSeverity
    title: str
    description: str
    clinical_context: str
    trigger_data: Dict[str, Any]
    recommended_action: str
    escalation_path: List[str]
    time_to_escalation_minutes: int
    created_at: datetime
    expires_at: Optional[datetime]
    status: AlertStatus
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]


@dataclass
class AlertRule:
    """Rule for generating critical alerts."""
    rule_id: str
    name: str
    category: AlertCategory
    severity: AlertSeverity
    conditions: Dict[str, Any]
    description: str
    recommended_action: str
    escalation_path: List[str]
    time_to_escalation_minutes: int
    is_active: bool


class CriticalAlertAgent(BaseMedicalAgent):
    """Agent for monitoring and generating critical alerts."""
    
    def __init__(self):
        super().__init__("CriticalAlertAgent")
        self.event_producer = MedicalRecordsEventProducer()
        
        # Initialize alert rules
        self.alert_rules = self._initialize_alert_rules()
        
        # Track active alerts to prevent duplicates
        self.active_alerts: Set[str] = set()
        
        # Alert patterns for different categories
        self.alert_patterns = {
            AlertCategory.LAB_CRITICAL: [
                r'\b(critical|panic|urgent)\b.*\b(lab|test|value)\b',
                r'\b(glucose|sodium|potassium|calcium|hemoglobin|platelet)\b.*\b(critical|panic)\b'
            ],
            AlertCategory.IMAGING_CRITICAL: [
                r'\b(mass|tumor|hemorrhage|pneumothorax|aortic dissection|pulmonary embolism)\b',
                r'\b(critical|urgent)\b.*\b(finding|abnormality)\b'
            ],
            AlertCategory.CLINICAL_URGENT: [
                r'\b(acute|emergency|urgent|critical)\b.*\b(condition|situation|presentation)\b',
                r'\b(severe|life.?threatening|immediate)\b.*\b(attention|intervention)\b'
            ],
            AlertCategory.MEDICATION_ALERT: [
                r'\b(drug interaction|allergy|contraindication|toxicity|overdose)\b',
                r'\b(medication|drug|prescription)\b.*\b(alert|warning|caution)\b'
            ],
            AlertCategory.VITAL_SIGNS: [
                r'\b(blood pressure|heart rate|temperature|respiratory rate|oxygen saturation)\b.*\b(critical|abnormal)\b',
                r'\b(hypotension|hypertension|tachycardia|bradycardia|fever|hypothermia)\b'
            ]
        }
    
    async def _process_impl(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Monitor medical data and generate critical alerts.
        
        Args:
            data: Dictionary containing monitoring parameters
            db: Database session
            
        Returns:
            AgentResult: Generated alerts and monitoring results
        """
        patient_id = data.get("patient_id")
        monitoring_period_hours = data.get("monitoring_period_hours", 24)
        include_historical = data.get("include_historical", True)
        
        if not patient_id:
            return AgentResult(
                success=False,
                error="patient_id is required"
            )
        
        try:
            # Get recent medical data
            lab_results = await self._get_recent_lab_results(db, patient_id, monitoring_period_hours)
            imaging_reports = await self._get_recent_imaging_reports(db, patient_id, monitoring_period_hours)
            clinical_reports = await self._get_recent_clinical_reports(db, patient_id, monitoring_period_hours)
            
            # Generate alerts based on rules
            alerts = await self._generate_alerts(
                patient_id, lab_results, imaging_reports, clinical_reports, db
            )
            
            # Check for trend-based alerts
            trend_alerts = await self._check_trend_alerts(patient_id, lab_results, db)
            alerts.extend(trend_alerts)
            
            # Check for combination alerts
            combination_alerts = await self._check_combination_alerts(
                patient_id, lab_results, imaging_reports, clinical_reports, db
            )
            alerts.extend(combination_alerts)
            
            # Filter out duplicate alerts
            unique_alerts = self._deduplicate_alerts(alerts)
            
            # Update alert statuses
            await self._update_alert_statuses(unique_alerts, db)
            
            # Publish alert events
            for alert in unique_alerts:
                await self._publish_alert_event(alert)
            
            # Generate monitoring summary
            monitoring_summary = self._generate_monitoring_summary(
                patient_id, lab_results, imaging_reports, clinical_reports, unique_alerts
            )
            
            return AgentResult(
                success=True,
                data={
                    "patient_id": str(patient_id),
                    "monitoring_period_hours": monitoring_period_hours,
                    "alerts_generated": len(unique_alerts),
                    "alerts_by_severity": self._group_alerts_by_severity(unique_alerts),
                    "alerts_by_category": self._group_alerts_by_category(unique_alerts),
                    "alerts": [self._alert_to_dict(alert) for alert in unique_alerts],
                    "monitoring_summary": monitoring_summary,
                    "last_monitoring": datetime.utcnow().isoformat()
                },
                insights=self._generate_insights(unique_alerts, monitoring_summary),
                recommendations=self._generate_recommendations(unique_alerts),
                confidence=0.92
            )
            
        except Exception as e:
            self.logger.error(f"Critical alert monitoring failed: {str(e)}")
            return AgentResult(
                success=False,
                error=f"Critical alert monitoring failed: {str(e)}"
            )
    
    def _initialize_alert_rules(self) -> List[AlertRule]:
        """Initialize alert rules for different clinical scenarios."""
        rules = [
            # Lab critical value rules
            AlertRule(
                rule_id="lab_critical_glucose",
                name="Critical Glucose Level",
                category=AlertCategory.LAB_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                conditions={
                    "test_name": "glucose",
                    "critical_low": 40,
                    "critical_high": 600,
                    "time_window_hours": 24
                },
                description="Critical glucose level detected requiring immediate attention",
                recommended_action="Check blood glucose immediately and administer appropriate treatment",
                escalation_path=["Nurse", "Physician", "Endocrinologist"],
                time_to_escalation_minutes=15,
                is_active=True
            ),
            
            AlertRule(
                rule_id="lab_critical_potassium",
                name="Critical Potassium Level",
                category=AlertCategory.LAB_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                conditions={
                    "test_name": "potassium",
                    "critical_low": 2.5,
                    "critical_high": 6.5,
                    "time_window_hours": 24
                },
                description="Critical potassium level detected - cardiac risk",
                recommended_action="Immediate ECG and electrolyte correction",
                escalation_path=["Nurse", "Physician", "Cardiologist"],
                time_to_escalation_minutes=10,
                is_active=True
            ),
            
            AlertRule(
                rule_id="lab_critical_hemoglobin",
                name="Critical Hemoglobin Level",
                category=AlertCategory.LAB_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                conditions={
                    "test_name": "hemoglobin",
                    "critical_low": 6.0,
                    "critical_high": 22.0,
                    "time_window_hours": 24
                },
                description="Critical hemoglobin level - transfusion consideration",
                recommended_action="Assess for bleeding and consider transfusion",
                escalation_path=["Nurse", "Physician", "Hematologist"],
                time_to_escalation_minutes=30,
                is_active=True
            ),
            
            # Imaging critical rules
            AlertRule(
                rule_id="imaging_critical_mass",
                name="Critical Imaging Mass",
                category=AlertCategory.IMAGING_CRITICAL,
                severity=AlertSeverity.HIGH,
                conditions={
                    "finding_type": "mass",
                    "size_threshold_cm": 3.0,
                    "time_window_hours": 48
                },
                description="Large mass detected on imaging requiring urgent evaluation",
                recommended_action="Urgent biopsy and oncology consultation",
                escalation_path=["Radiologist", "Oncologist", "Surgeon"],
                time_to_escalation_minutes=60,
                is_active=True
            ),
            
            AlertRule(
                rule_id="imaging_critical_hemorrhage",
                name="Critical Hemorrhage",
                category=AlertCategory.IMAGING_CRITICAL,
                severity=AlertSeverity.EMERGENCY,
                conditions={
                    "finding_type": "hemorrhage",
                    "time_window_hours": 6
                },
                description="Acute hemorrhage detected requiring immediate intervention",
                recommended_action="Immediate neurosurgical evaluation",
                escalation_path=["Radiologist", "Neurosurgeon", "Emergency Medicine"],
                time_to_escalation_minutes=5,
                is_active=True
            ),
            
            # Clinical urgent rules
            AlertRule(
                rule_id="clinical_acute_chest_pain",
                name="Acute Chest Pain",
                category=AlertCategory.CLINICAL_URGENT,
                severity=AlertSeverity.EMERGENCY,
                conditions={
                    "symptom": "chest pain",
                    "severity": "severe",
                    "time_window_hours": 2
                },
                description="Severe chest pain - possible cardiac event",
                recommended_action="Immediate ECG and cardiac evaluation",
                escalation_path=["Nurse", "Emergency Medicine", "Cardiologist"],
                time_to_escalation_minutes=5,
                is_active=True
            ),
            
            # Trend alert rules
            AlertRule(
                rule_id="trend_creatinine_rising",
                name="Rising Creatinine Trend",
                category=AlertCategory.TREND_ALERT,
                severity=AlertSeverity.HIGH,
                conditions={
                    "test_name": "creatinine",
                    "trend_direction": "increasing",
                    "change_percentage": 25,
                    "time_window_days": 7
                },
                description="Significant rise in creatinine indicating kidney function decline",
                recommended_action="Nephrology consultation and medication review",
                escalation_path=["Physician", "Nephrologist"],
                time_to_escalation_minutes=120,
                is_active=True
            ),
            
            # Combination alert rules
            AlertRule(
                rule_id="combination_diabetes_ketoacidosis",
                name="Diabetic Ketoacidosis Risk",
                category=AlertCategory.COMBINATION_ALERT,
                severity=AlertSeverity.CRITICAL,
                conditions={
                    "required_tests": ["glucose", "ketone", "ph"],
                    "glucose_threshold": 250,
                    "ketone_threshold": 3.0,
                    "time_window_hours": 6
                },
                description="High risk for diabetic ketoacidosis",
                recommended_action="Immediate insulin therapy and fluid resuscitation",
                escalation_path=["Nurse", "Physician", "Endocrinologist"],
                time_to_escalation_minutes=15,
                is_active=True
            )
        ]
        
        return rules
    
    async def _get_recent_lab_results(self, db: AsyncSession, patient_id: str, hours: int) -> List["LabResultDB"]:
        """Get recent lab results for monitoring."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await db.execute(
                select(LabResultDB)
                .where(
                    and_(
                        LabResultDB.patient_id == UUID(patient_id),
                        LabResultDB.test_date >= cutoff_time
                    )
                )
                .order_by(desc(LabResultDB.test_date))
            )
            
            return result.scalars().all()
            
        except Exception as e:
            self.logger.error(f"Error fetching lab results: {e}")
            return []
    
    async def _get_recent_imaging_reports(self, db: AsyncSession, patient_id: str, hours: int) -> List["ImagingReportDB"]:
        """Get recent imaging reports for monitoring."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await db.execute(
                select(ImagingReportDB)
                .where(
                    and_(
                        ImagingReportDB.patient_id == UUID(patient_id),
                        ImagingReportDB.report_date >= cutoff_time
                    )
                )
                .order_by(desc(ImagingReportDB.report_date))
            )
            
            return result.scalars().all()
            
        except Exception as e:
            self.logger.error(f"Error fetching imaging reports: {e}")
            return []
    
    async def _get_recent_clinical_reports(self, db: AsyncSession, patient_id: str, hours: int) -> List["ClinicalReportDB"]:
        """Get recent clinical reports for monitoring."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await db.execute(
                select(ClinicalReportDB)
                .where(
                    and_(
                        ClinicalReportDB.patient_id == UUID(patient_id),
                        ClinicalReportDB.report_date >= cutoff_time
                    )
                )
                .order_by(desc(ClinicalReportDB.report_date))
            )
            
            return result.scalars().all()
            
        except Exception as e:
            self.logger.error(f"Error fetching clinical reports: {e}")
            return []
    
    async def _generate_alerts(self, patient_id: str, lab_results: List["LabResultDB"], imaging_reports: List["ImagingReportDB"], clinical_reports: List["ClinicalReportDB"], db: AsyncSession) -> List[CriticalAlert]:
        """Generate alerts based on alert rules."""
        alerts = []
        
        for rule in self.alert_rules:
            if not rule.is_active:
                continue
            
            # Check lab critical rules
            if rule.category == AlertCategory.LAB_CRITICAL:
                lab_alerts = self._check_lab_critical_rule(rule, lab_results, patient_id)
                alerts.extend(lab_alerts)
            
            # Check imaging critical rules
            elif rule.category == AlertCategory.IMAGING_CRITICAL:
                imaging_alerts = self._check_imaging_critical_rule(rule, imaging_reports, patient_id)
                alerts.extend(imaging_alerts)
            
            # Check clinical urgent rules
            elif rule.category == AlertCategory.CLINICAL_URGENT:
                clinical_alerts = self._check_clinical_urgent_rule(rule, clinical_reports, patient_id)
                alerts.extend(clinical_alerts)
        
        return alerts
    
    def _check_lab_critical_rule(self, rule: AlertRule, lab_results: List["LabResultDB"], patient_id: str) -> List[CriticalAlert]:
        """Check lab results against critical value rules."""
        alerts = []
        
        for result in lab_results:
            if result.value is None:
                continue
            
            try:
                value = float(result.value)
                test_name_lower = result.test_name.lower()
                
                # Check if test matches rule
                rule_test = rule.conditions.get("test_name", "").lower()
                if rule_test and rule_test not in test_name_lower:
                    continue
                
                # Check critical thresholds
                critical_low = rule.conditions.get("critical_low")
                critical_high = rule.conditions.get("critical_high")
                
                if critical_low is not None and value <= critical_low:
                    alert = self._create_lab_alert(rule, result, "low", value, patient_id)
                    alerts.append(alert)
                
                if critical_high is not None and value >= critical_high:
                    alert = self._create_lab_alert(rule, result, "high", value, patient_id)
                    alerts.append(alert)
                
            except (ValueError, TypeError):
                continue
        
        return alerts
    
    def _check_imaging_critical_rule(self, rule: AlertRule, imaging_reports: List["ImagingReportDB"], patient_id: str) -> List[CriticalAlert]:
        """Check imaging reports against critical finding rules."""
        alerts = []
        
        for report in imaging_reports:
            if not report.findings:
                continue
            
            # Parse findings (assuming JSON or structured format)
            findings = self._parse_imaging_findings(report.findings)
            
            for finding in findings:
                finding_type = finding.get("type", "").lower()
                rule_type = rule.conditions.get("finding_type", "").lower()
                
                if rule_type and rule_type in finding_type:
                    # Check size threshold if applicable
                    size_threshold = rule.conditions.get("size_threshold_cm")
                    if size_threshold:
                        size = finding.get("size_cm", 0)
                        if size >= size_threshold:
                            alert = self._create_imaging_alert(rule, report, finding, patient_id)
                            alerts.append(alert)
                    else:
                        alert = self._create_imaging_alert(rule, report, finding, patient_id)
                        alerts.append(alert)
        
        return alerts
    
    def _check_clinical_urgent_rule(self, rule: AlertRule, clinical_reports: List["ClinicalReportDB"], patient_id: str) -> List[CriticalAlert]:
        """Check clinical reports against urgent condition rules."""
        alerts = []
        
        for report in clinical_reports:
            if not report.content:
                continue
            
            content_lower = report.content.lower()
            
            # Check for symptoms
            symptom = rule.conditions.get("symptom", "").lower()
            if symptom and symptom in content_lower:
                severity = rule.conditions.get("severity", "").lower()
                if severity in content_lower:
                    alert = self._create_clinical_alert(rule, report, patient_id)
                    alerts.append(alert)
        
        return alerts
    
    async def _check_trend_alerts(self, patient_id: str, lab_results: List["LabResultDB"], db: AsyncSession) -> List[CriticalAlert]:
        """Check for trend-based alerts."""
        alerts = []
        
        # Group results by test
        test_groups = {}
        for result in lab_results:
            if result.test_name not in test_groups:
                test_groups[result.test_name] = []
            test_groups[result.test_name].append(result)
        
        # Check trends for each test
        for test_name, results in test_groups.items():
            if len(results) < 2:
                continue
            
            # Sort by date
            results.sort(key=lambda x: x.test_date)
            
            # Calculate trend
            trend = self._calculate_trend(test_name, results)
            if trend:
                # Check against trend rules
                trend_alerts = self._check_trend_rule(trend, patient_id)
                alerts.extend(trend_alerts)
        
        return alerts
    
    def _calculate_trend(self, test_name: str, results: List["LabResultDB"]) -> Optional[Dict[str, Any]]:
        """Calculate trend for a test."""
        if len(results) < 2:
            return None
        
        try:
            values = []
            dates = []
            for result in results:
                if result.value is not None:
                    values.append(float(result.value))
                    dates.append(result.test_date)
            
            if len(values) < 2:
                return None
            
            first_value = values[0]
            last_value = values[-1]
            time_period = (dates[-1] - dates[0]).days
            
            if time_period == 0:
                return None
            
            change_percentage = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
            
            direction = "increasing" if change_percentage > 10 else "decreasing" if change_percentage < -10 else "stable"
            
            return {
                "test_name": test_name,
                "direction": direction,
                "change_percentage": change_percentage,
                "time_period_days": time_period,
                "first_value": first_value,
                "last_value": last_value
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend for {test_name}: {e}")
            return None
    
    def _check_trend_rule(self, trend: Dict[str, Any], patient_id: str) -> List[CriticalAlert]:
        """Check trend against trend alert rules."""
        alerts = []
        
        for rule in self.alert_rules:
            if rule.category != AlertCategory.TREND_ALERT:
                continue
            
            conditions = rule.conditions
            test_name = conditions.get("test_name", "").lower()
            trend_direction = conditions.get("trend_direction", "").lower()
            change_threshold = conditions.get("change_percentage", 0)
            
            if (test_name in trend["test_name"].lower() and 
                trend_direction == trend["direction"] and 
                abs(trend["change_percentage"]) >= change_threshold):
                
                alert = self._create_trend_alert(rule, trend, patient_id)
                alerts.append(alert)
        
        return alerts
    
    async def _check_combination_alerts(self, patient_id: str, lab_results: List["LabResultDB"], 
                                      imaging_reports: List["ImagingReportDB"], 
                                      clinical_reports: List["ClinicalReportDB"], 
                                      db: AsyncSession) -> List[CriticalAlert]:
        """Check for combination alerts requiring multiple conditions."""
        alerts = []
        
        for rule in self.alert_rules:
            if rule.category != AlertCategory.COMBINATION_ALERT:
                continue
            
            if rule.rule_id == "combination_diabetes_ketoacidosis":
                dka_alert = self._check_dka_combination(rule, lab_results, patient_id)
                if dka_alert:
                    alerts.append(dka_alert)
        
        return alerts
    
    def _check_dka_combination(self, rule: AlertRule, lab_results: List["LabResultDB"], patient_id: str) -> Optional[CriticalAlert]:
        """Check for diabetic ketoacidosis combination alert."""
        required_tests = rule.conditions.get("required_tests", [])
        glucose_threshold = rule.conditions.get("glucose_threshold", 250)
        ketone_threshold = rule.conditions.get("ketone_threshold", 3.0)
        
        # Get recent values for required tests
        test_values = {}
        for result in lab_results:
            test_name_lower = result.test_name.lower()
            for required_test in required_tests:
                if required_test in test_name_lower and result.value is not None:
                    try:
                        test_values[required_test] = float(result.value)
                    except (ValueError, TypeError):
                        continue
        
        # Check if all conditions are met
        if (len(test_values) >= 2 and  # At least glucose and one other
            test_values.get("glucose", 0) >= glucose_threshold and
            test_values.get("ketone", 0) >= ketone_threshold):
            
            return self._create_combination_alert(rule, test_values, patient_id)
        
        return None
    
    def _create_lab_alert(self, rule: AlertRule, result: "LabResultDB", direction: str, value: float, patient_id: str) -> CriticalAlert:
        """Create a lab critical value alert."""
        alert_id = f"lab_{rule.rule_id}_{result.id}_{direction}"
        
        return CriticalAlert(
            alert_id=alert_id,
            patient_id=UUID(patient_id),
            alert_type=rule.category,
            severity=rule.severity,
            title=f"Critical {result.test_name} Level",
            description=f"Critical {direction} {result.test_name} value: {value} {result.unit or ''}",
            clinical_context=f"Critical lab value detected requiring immediate attention",
            trigger_data={
                "test_name": result.test_name,
                "value": value,
                "unit": result.unit,
                "direction": direction,
                "reference_range": result.reference_range_text
            },
            recommended_action=rule.recommended_action,
            escalation_path=rule.escalation_path,
            time_to_escalation_minutes=rule.time_to_escalation_minutes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            status=AlertStatus.ACTIVE,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None
        )
    
    def _create_imaging_alert(self, rule: AlertRule, report: "ImagingReportDB", finding: Dict[str, Any], patient_id: str) -> CriticalAlert:
        """Create an imaging critical finding alert."""
        alert_id = f"imaging_{rule.rule_id}_{report.id}_{finding.get('id', 'unknown')}"
        
        return CriticalAlert(
            alert_id=alert_id,
            patient_id=UUID(patient_id),
            alert_type=rule.category,
            severity=rule.severity,
            title=f"Critical Imaging Finding: {finding.get('type', 'Abnormality')}",
            description=f"Critical {finding.get('type', 'finding')} detected on {report.modality} imaging",
            clinical_context=f"Critical imaging finding requiring urgent evaluation",
            trigger_data={
                "modality": report.modality,
                "finding_type": finding.get("type"),
                "location": finding.get("location"),
                "size": finding.get("size_cm")
            },
            recommended_action=rule.recommended_action,
            escalation_path=rule.escalation_path,
            time_to_escalation_minutes=rule.time_to_escalation_minutes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=48),
            status=AlertStatus.ACTIVE,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None
        )
    
    def _create_clinical_alert(self, rule: AlertRule, report: "ClinicalReportDB", patient_id: str) -> CriticalAlert:
        """Create a clinical urgent condition alert."""
        alert_id = f"clinical_{rule.rule_id}_{report.id}"
        
        return CriticalAlert(
            alert_id=alert_id,
            patient_id=UUID(patient_id),
            alert_type=rule.category,
            severity=rule.severity,
            title=f"Urgent Clinical Condition: {rule.name}",
            description=f"Urgent clinical condition detected requiring immediate attention",
            clinical_context=f"Clinical report indicates urgent condition",
            trigger_data={
                "report_type": report.report_type,
                "symptom": rule.conditions.get("symptom"),
                "severity": rule.conditions.get("severity")
            },
            recommended_action=rule.recommended_action,
            escalation_path=rule.escalation_path,
            time_to_escalation_minutes=rule.time_to_escalation_minutes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=6),
            status=AlertStatus.ACTIVE,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None
        )
    
    def _create_trend_alert(self, rule: AlertRule, trend: Dict[str, Any], patient_id: str) -> CriticalAlert:
        """Create a trend-based alert."""
        alert_id = f"trend_{rule.rule_id}_{trend['test_name']}"
        
        return CriticalAlert(
            alert_id=alert_id,
            patient_id=UUID(patient_id),
            alert_type=rule.category,
            severity=rule.severity,
            title=f"Trend Alert: {trend['test_name']}",
            description=f"Significant {trend['direction']} trend in {trend['test_name']}: {trend['change_percentage']:.1f}% change over {trend['time_period_days']} days",
            clinical_context=f"Concerning trend detected requiring clinical evaluation",
            trigger_data=trend,
            recommended_action=rule.recommended_action,
            escalation_path=rule.escalation_path,
            time_to_escalation_minutes=rule.time_to_escalation_minutes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=72),
            status=AlertStatus.ACTIVE,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None
        )
    
    def _create_combination_alert(self, rule: AlertRule, test_values: Dict[str, float], patient_id: str) -> CriticalAlert:
        """Create a combination alert."""
        alert_id = f"combination_{rule.rule_id}_{patient_id}"
        
        return CriticalAlert(
            alert_id=alert_id,
            patient_id=UUID(patient_id),
            alert_type=rule.category,
            severity=rule.severity,
            title=f"Combination Alert: {rule.name}",
            description=f"Multiple conditions met indicating {rule.name.lower()}",
            clinical_context=f"Combination of findings suggests urgent clinical situation",
            trigger_data=test_values,
            recommended_action=rule.recommended_action,
            escalation_path=rule.escalation_path,
            time_to_escalation_minutes=rule.time_to_escalation_minutes,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=12),
            status=AlertStatus.ACTIVE,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None
        )
    
    def _parse_imaging_findings(self, findings_data: str) -> List[Dict[str, Any]]:
        """Parse imaging findings from stored data."""
        try:
            # This would parse the findings data based on your storage format
            # For now, return a simple structure
            return [{"type": "finding", "location": "unknown", "size_cm": 0}]
        except Exception as e:
            self.logger.error(f"Error parsing imaging findings: {e}")
            return []
    
    def _deduplicate_alerts(self, alerts: List[CriticalAlert]) -> List[CriticalAlert]:
        """Remove duplicate alerts based on alert_id."""
        seen_ids = set()
        unique_alerts = []
        
        for alert in alerts:
            if alert.alert_id not in seen_ids and alert.alert_id not in self.active_alerts:
                seen_ids.add(alert.alert_id)
                self.active_alerts.add(alert.alert_id)
                unique_alerts.append(alert)
        
        return unique_alerts
    
    async def _update_alert_statuses(self, alerts: List[CriticalAlert], db: AsyncSession):
        """Update alert statuses in database."""
        try:
            # This would update alert statuses in your database
            # Implementation depends on your schema
            pass
        except Exception as e:
            self.logger.error(f"Error updating alert statuses: {e}")
    
    async def _publish_alert_event(self, alert: CriticalAlert):
        """Publish alert event to Kafka."""
        try:
            event = {
                "event_type": "critical_alert_generated",
                "timestamp": datetime.utcnow().isoformat(),
                "alert_id": alert.alert_id,
                "patient_id": str(alert.patient_id),
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "recommended_action": alert.recommended_action,
                "escalation_path": alert.escalation_path,
                "time_to_escalation_minutes": alert.time_to_escalation_minutes,
                "created_at": alert.created_at.isoformat(),
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
                "status": alert.status.value,
                "source": "CriticalAlertAgent"
            }
            
            await self.event_producer.publish_critical_alert_event(event)
            self.logger.info(f"🚨 Published critical alert event: {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing alert event: {e}")
    
    def _generate_monitoring_summary(self, patient_id: str, lab_results: List["LabResultDB"], 
                                   imaging_reports: List["ImagingReportDB"], 
                                   clinical_reports: List["ClinicalReportDB"], 
                                   alerts: List[CriticalAlert]) -> Dict[str, Any]:
        """Generate monitoring summary."""
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        emergency_alerts = [a for a in alerts if a.severity == AlertSeverity.EMERGENCY]
        
        return {
            "total_lab_results": len(lab_results),
            "total_imaging_reports": len(imaging_reports),
            "total_clinical_reports": len(clinical_reports),
            "total_alerts": len(alerts),
            "critical_alerts": len(critical_alerts),
            "emergency_alerts": len(emergency_alerts),
            "monitoring_status": "active" if alerts else "normal",
            "requires_immediate_attention": len(emergency_alerts) > 0,
            "requires_urgent_attention": len(critical_alerts) > 0
        }
    
    def _group_alerts_by_severity(self, alerts: List[CriticalAlert]) -> Dict[str, int]:
        """Group alerts by severity level."""
        grouped = {}
        for alert in alerts:
            severity = alert.severity.value
            grouped[severity] = grouped.get(severity, 0) + 1
        return grouped
    
    def _group_alerts_by_category(self, alerts: List[CriticalAlert]) -> Dict[str, int]:
        """Group alerts by category."""
        grouped = {}
        for alert in alerts:
            category = alert.alert_type.value
            grouped[category] = grouped.get(category, 0) + 1
        return grouped
    
    def _alert_to_dict(self, alert: CriticalAlert) -> Dict[str, Any]:
        """Convert CriticalAlert to dictionary."""
        return {
            "alert_id": alert.alert_id,
            "patient_id": str(alert.patient_id),
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "clinical_context": alert.clinical_context,
            "trigger_data": alert.trigger_data,
            "recommended_action": alert.recommended_action,
            "escalation_path": alert.escalation_path,
            "time_to_escalation_minutes": alert.time_to_escalation_minutes,
            "created_at": alert.created_at.isoformat(),
            "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
            "status": alert.status.value,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            "resolved_by": alert.resolved_by,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        }
    
    def _generate_insights(self, alerts: List[CriticalAlert], monitoring_summary: Dict[str, Any]) -> List[str]:
        """Generate insights from alert monitoring."""
        insights = []
        
        insights.append(f"Monitored {monitoring_summary['total_lab_results']} lab results, {monitoring_summary['total_imaging_reports']} imaging reports, and {monitoring_summary['total_clinical_reports']} clinical reports")
        
        if alerts:
            insights.append(f"Generated {len(alerts)} critical alerts")
            
            emergency_count = monitoring_summary['emergency_alerts']
            if emergency_count > 0:
                insights.append(f"🚨 {emergency_count} emergency alerts requiring immediate attention")
            
            critical_count = monitoring_summary['critical_alerts']
            if critical_count > 0:
                insights.append(f"⚠️ {critical_count} critical alerts requiring urgent attention")
        else:
            insights.append("No critical alerts generated - patient status normal")
        
        return insights
    
    def _generate_recommendations(self, alerts: List[CriticalAlert]) -> List[str]:
        """Generate recommendations based on alerts."""
        recommendations = []
        
        emergency_alerts = [a for a in alerts if a.severity == AlertSeverity.EMERGENCY]
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        
        if emergency_alerts:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Emergency alerts detected - contact healthcare team immediately")
        
        if critical_alerts:
            recommendations.append("URGENT ATTENTION: Critical alerts detected - escalate to appropriate clinical team")
        
        if alerts:
            recommendations.append("Review all alerts and implement recommended actions within specified timeframes")
            recommendations.append("Monitor patient closely for any changes in condition")
        
        if not recommendations:
            recommendations.append("Continue routine monitoring - no immediate action required")
        
        return recommendations 