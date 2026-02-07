"""
Pattern Detection Agent
Advanced AI agent for detecting health patterns and behavioral trends.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import numpy as np
from scipy import signal
from scipy.stats import pearsonr
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_insight_agent import BaseInsightAgent, AgentResult, AgentStatus, AgentPriority
from ..models.insight_models import (
    HealthPatternDB, InsightType, InsightSeverity, InsightStatus, InsightCategory
)
from common.utils.logging import get_logger


class PatternDetectionAgent(BaseInsightAgent):
    """Advanced AI agent for detecting health patterns and behavioral trends."""
    
    def __init__(self):
        super().__init__(
            agent_name="pattern_detector",
            priority=AgentPriority.HIGH
        )
        
        # Pattern detection algorithms
        self.pattern_algorithms = self._initialize_pattern_algorithms()
        self.pattern_templates = self._load_pattern_templates()
        self.pattern_thresholds = self._load_pattern_thresholds()
        
        # Behavioral analysis models
        self.behavioral_models = self._initialize_behavioral_models()
        
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return [
            "temporal_pattern_detection",
            "behavioral_pattern_analysis",
            "cyclic_pattern_identification",
            "seasonal_pattern_detection",
            "clustering_analysis",
            "correlation_pattern_detection",
            "anomaly_pattern_detection",
            "trend_pattern_analysis",
            "multi_variate_pattern_detection",
            "pattern_classification"
        ]
    
    def _get_data_requirements(self) -> List[str]:
        """Get list of required data sources."""
        return [
            "patient_id",
            "time_series_data",
            "vital_signs",
            "activity_data",
            "sleep_data",
            "nutrition_data",
            "medication_data",
            "symptom_data"
        ]
    
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output schema for the agent."""
        return {
            "patterns": [
                {
                    "pattern_type": "string",
                    "pattern_name": "string",
                    "description": "string",
                    "confidence_score": "float",
                    "frequency": "string",
                    "duration": "string",
                    "pattern_data": "object",
                    "detection_method": "string",
                    "data_sources": "array"
                }
            ],
            "metadata": {
                "total_patterns": "integer",
                "patterns_by_type": "object",
                "average_confidence": "float",
                "detection_timestamp": "string"
            }
        }
    
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute pattern detection analysis.
        
        Args:
            data: Input health data
            db: Database session
            
        Returns:
            AgentResult: Detected patterns
        """
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"🚀 Starting pattern detection for patient {data.get('patient_id')}")
            
            # Preprocess data
            processed_data = await self.preprocess_data(data)
            
            # Detect various types of patterns
            patterns = []
            
            # Temporal patterns
            temporal_patterns = await self._detect_temporal_patterns(processed_data)
            patterns.extend(temporal_patterns)
            
            # Behavioral patterns
            behavioral_patterns = await self._detect_behavioral_patterns(processed_data)
            patterns.extend(behavioral_patterns)
            
            # Cyclic patterns
            cyclic_patterns = await self._detect_cyclic_patterns(processed_data)
            patterns.extend(cyclic_patterns)
            
            # Seasonal patterns
            seasonal_patterns = await self._detect_seasonal_patterns(processed_data)
            patterns.extend(seasonal_patterns)
            
            # Correlation patterns
            correlation_patterns = await self._detect_correlation_patterns(processed_data)
            patterns.extend(correlation_patterns)
            
            # Cluster patterns
            cluster_patterns = await self._detect_cluster_patterns(processed_data)
            patterns.extend(cluster_patterns)
            
            # Score and rank patterns
            scored_patterns = await self._score_patterns(patterns, processed_data)
            ranked_patterns = self._rank_patterns(scored_patterns)
            
            # Save patterns to database
            saved_patterns = await self._save_patterns(ranked_patterns, data['patient_id'], db)
            
            # Update status
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            # Create result
            result = AgentResult(
                success=True,
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                patterns=ranked_patterns,
                data={
                    'total_patterns': len(ranked_patterns),
                    'patterns_by_type': self._count_by_type(ranked_patterns),
                    'average_confidence': self._calculate_average_confidence(ranked_patterns),
                    'detection_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Postprocess results
            result = await self.postprocess_results(result)
            
            self.logger.info(f"✅ Pattern detection completed: {len(ranked_patterns)} patterns detected")
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Pattern detection failed: {str(e)}")
            
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _initialize_pattern_algorithms(self) -> Dict[str, Any]:
        """Initialize pattern detection algorithms."""
        return {
            "fourier_analysis": {
                "type": "frequency_domain",
                "parameters": {
                    "window_size": 24,  # hours
                    "min_frequency": 0.01,
                    "max_frequency": 0.5
                }
            },
            "wavelet_analysis": {
                "type": "time_frequency",
                "parameters": {
                    "wavelet_type": "db4",
                    "levels": 8,
                    "threshold": 0.1
                }
            },
            "autocorrelation": {
                "type": "temporal_correlation",
                "parameters": {
                    "max_lag": 48,
                    "confidence_level": 0.95
                }
            },
            "clustering": {
                "type": "spatial_clustering",
                "parameters": {
                    "n_clusters": 5,
                    "random_state": 42,
                    "n_init": 10
                }
            },
            "changepoint_detection": {
                "type": "structural_breaks",
                "parameters": {
                    "penalty": "BIC",
                    "min_segment_length": 6
                }
            }
        }
    
    def _load_pattern_templates(self) -> Dict[str, Any]:
        """Load pattern description templates."""
        return {
            "temporal": {
                "daily": "Daily pattern detected in {metric} with peak at {peak_time}",
                "weekly": "Weekly pattern detected in {metric} with {pattern_description}",
                "monthly": "Monthly pattern detected in {metric} showing {pattern_description}",
                "seasonal": "Seasonal pattern detected in {metric} with {seasonal_variation}"
            },
            "behavioral": {
                "routine": "Routine behavioral pattern detected in {activity}",
                "irregular": "Irregular behavioral pattern detected in {activity}",
                "optimal": "Optimal behavioral pattern detected in {activity}",
                "suboptimal": "Suboptimal behavioral pattern detected in {activity}"
            },
            "cyclic": {
                "circadian": "Circadian rhythm detected in {metric}",
                "ultradian": "Ultradian rhythm detected in {metric}",
                "infradian": "Infradian rhythm detected in {metric}"
            },
            "correlation": {
                "positive": "Positive correlation pattern between {metric1} and {metric2}",
                "negative": "Negative correlation pattern between {metric1} and {metric2}",
                "lagged": "Lagged correlation pattern between {metric1} and {metric2}"
            }
        }
    
    def _load_pattern_thresholds(self) -> Dict[str, Any]:
        """Load pattern detection thresholds."""
        return {
            "confidence": {
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            },
            "frequency": {
                "daily": 0.9,
                "weekly": 0.7,
                "monthly": 0.5
            },
            "correlation": {
                "strong": 0.7,
                "moderate": 0.5,
                "weak": 0.3
            },
            "clustering": {
                "silhouette_score": 0.5,
                "inertia_threshold": 0.1
            }
        }
    
    def _initialize_behavioral_models(self) -> Dict[str, Any]:
        """Initialize behavioral analysis models."""
        return {
            "activity_patterns": {
                "metrics": ["steps", "calories", "active_minutes", "exercise_sessions"],
                "patterns": ["consistent", "variable", "increasing", "decreasing", "optimal"]
            },
            "sleep_patterns": {
                "metrics": ["sleep_duration", "sleep_quality", "sleep_efficiency", "sleep_latency"],
                "patterns": ["regular", "irregular", "insufficient", "optimal", "disturbed"]
            },
            "nutrition_patterns": {
                "metrics": ["calorie_intake", "macronutrients", "meal_timing", "hydration"],
                "patterns": ["balanced", "unbalanced", "regular", "irregular", "optimal"]
            },
            "medication_patterns": {
                "metrics": ["adherence", "timing", "effectiveness", "side_effects"],
                "patterns": ["compliant", "non_compliant", "optimal", "suboptimal"]
            }
        }
    
    async def _detect_temporal_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect temporal patterns in time series data."""
        patterns = []
        
        # Analyze vital signs temporal patterns
        if 'vital_signs' in data:
            vital_patterns = self._analyze_vital_signs_temporal_patterns(data['vital_signs'])
            patterns.extend(vital_patterns)
        
        # Analyze activity temporal patterns
        if 'activity_data' in data:
            activity_patterns = self._analyze_activity_temporal_patterns(data['activity_data'])
            patterns.extend(activity_patterns)
        
        # Analyze sleep temporal patterns
        if 'sleep_data' in data:
            sleep_patterns = self._analyze_sleep_temporal_patterns(data['sleep_data'])
            patterns.extend(sleep_patterns)
        
        return patterns
    
    def _analyze_vital_signs_temporal_patterns(self, vital_signs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze temporal patterns in vital signs."""
        patterns = []
        
        # Group by metric
        metrics = {}
        for record in vital_signs:
            metric = record.get('metric')
            if metric not in metrics:
                metrics[metric] = []
            metrics[metric].append(record)
        
        for metric, records in metrics.items():
            if len(records) < 24:  # Need at least 24 data points
                continue
            
            # Sort by timestamp
            sorted_records = sorted(records, key=lambda x: x.get('timestamp', ''))
            values = [r.get('value', 0) for r in sorted_records]
            timestamps = [r.get('timestamp', '') for r in sorted_records]
            
            # Detect daily patterns
            daily_pattern = self._detect_daily_pattern(values, timestamps)
            if daily_pattern:
                patterns.append({
                    'pattern_type': 'temporal',
                    'pattern_name': f"{metric}_daily_pattern",
                    'description': f"Daily pattern detected in {metric}",
                    'confidence_score': daily_pattern['confidence'],
                    'frequency': 'daily',
                    'duration': '24 hours',
                    'pattern_data': daily_pattern,
                    'detection_method': 'autocorrelation',
                    'data_sources': ['vital_signs']
                })
            
            # Detect weekly patterns
            weekly_pattern = self._detect_weekly_pattern(values, timestamps)
            if weekly_pattern:
                patterns.append({
                    'pattern_type': 'temporal',
                    'pattern_name': f"{metric}_weekly_pattern",
                    'description': f"Weekly pattern detected in {metric}",
                    'confidence_score': weekly_pattern['confidence'],
                    'frequency': 'weekly',
                    'duration': '7 days',
                    'pattern_data': weekly_pattern,
                    'detection_method': 'fourier_analysis',
                    'data_sources': ['vital_signs']
                })
        
        return patterns
    
    def _detect_daily_pattern(self, values: List[float], timestamps: List[str]) -> Optional[Dict[str, Any]]:
        """Detect daily patterns using autocorrelation."""
        if len(values) < 24:
            return None
        
        # Calculate autocorrelation
        autocorr = np.correlate(values, values, mode='full')
        autocorr = autocorr[len(values)-1:]
        
        # Normalize
        autocorr = autocorr / autocorr[0]
        
        # Look for daily periodicity (24-hour cycle)
        daily_lag = 24
        if len(autocorr) > daily_lag:
            daily_correlation = autocorr[daily_lag]
            
            if daily_correlation > 0.5:  # Strong daily pattern
                return {
                    'type': 'daily',
                    'lag': daily_lag,
                    'correlation': daily_correlation,
                    'confidence': min(daily_correlation, 1.0),
                    'peak_hour': self._find_peak_hour(values, timestamps),
                    'trough_hour': self._find_trough_hour(values, timestamps)
                }
        
        return None
    
    def _detect_weekly_pattern(self, values: List[float], timestamps: List[str]) -> Optional[Dict[str, Any]]:
        """Detect weekly patterns using Fourier analysis."""
        if len(values) < 168:  # Need at least a week of hourly data
            return None
        
        # Perform FFT
        fft = np.fft.fft(values)
        freqs = np.fft.fftfreq(len(values))
        
        # Look for weekly frequency (1/168 = 0.006 Hz)
        weekly_freq = 1/168
        freq_tolerance = 0.001
        
        weekly_indices = np.where(np.abs(freqs - weekly_freq) < freq_tolerance)[0]
        
        if len(weekly_indices) > 0:
            # Calculate power at weekly frequency
            power = np.abs(fft[weekly_indices[0]]) ** 2
            total_power = np.sum(np.abs(fft) ** 2)
            
            if total_power > 0:
                relative_power = power / total_power
                
                if relative_power > 0.1:  # Significant weekly pattern
                    return {
                        'type': 'weekly',
                        'frequency': weekly_freq,
                        'power': power,
                        'relative_power': relative_power,
                        'confidence': min(relative_power * 5, 1.0),  # Scale to 0-1
                        'weekday_variation': self._calculate_weekday_variation(values, timestamps)
                    }
        
        return None
    
    def _find_peak_hour(self, values: List[float], timestamps: List[str]) -> Optional[int]:
        """Find the hour of day with peak values."""
        if len(values) < 24:
            return None
        
        # Group by hour of day
        hourly_values = {}
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                if hour not in hourly_values:
                    hourly_values[hour] = []
                hourly_values[hour].append(value)
            except:
                continue
        
        # Find hour with highest average value
        if hourly_values:
            avg_by_hour = {hour: np.mean(vals) for hour, vals in hourly_values.items()}
            peak_hour = max(avg_by_hour.items(), key=lambda x: x[1])[0]
            return peak_hour
        
        return None
    
    def _find_trough_hour(self, values: List[float], timestamps: List[str]) -> Optional[int]:
        """Find the hour of day with lowest values."""
        if len(values) < 24:
            return None
        
        # Group by hour of day
        hourly_values = {}
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                if hour not in hourly_values:
                    hourly_values[hour] = []
                hourly_values[hour].append(value)
            except:
                continue
        
        # Find hour with lowest average value
        if hourly_values:
            avg_by_hour = {hour: np.mean(vals) for hour, vals in hourly_values.items()}
            trough_hour = min(avg_by_hour.items(), key=lambda x: x[1])[0]
            return trough_hour
        
        return None
    
    def _calculate_weekday_variation(self, values: List[float], timestamps: List[str]) -> Dict[str, float]:
        """Calculate variation by day of week."""
        weekday_values = {}
        
        for value, timestamp in zip(values, timestamps):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                weekday = dt.strftime('%A')
                if weekday not in weekday_values:
                    weekday_values[weekday] = []
                weekday_values[weekday].append(value)
            except:
                continue
        
        return {day: np.mean(vals) for day, vals in weekday_values.items()}
    
    async def _detect_behavioral_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect behavioral patterns in activity and lifestyle data."""
        patterns = []
        
        # Activity patterns
        if 'activity_data' in data:
            activity_patterns = self._analyze_activity_patterns(data['activity_data'])
            patterns.extend(activity_patterns)
        
        # Sleep patterns
        if 'sleep_data' in data:
            sleep_patterns = self._analyze_sleep_patterns(data['sleep_data'])
            patterns.extend(sleep_patterns)
        
        # Nutrition patterns
        if 'nutrition_data' in data:
            nutrition_patterns = self._analyze_nutrition_patterns(data['nutrition_data'])
            patterns.extend(nutrition_patterns)
        
        return patterns
    
    def _analyze_activity_patterns(self, activity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze activity behavioral patterns."""
        patterns = []
        
        if len(activity_data) < 7:
            return patterns
        
        # Calculate daily activity metrics
        daily_activity = {}
        for record in activity_data:
            date = record.get('date', record.get('timestamp', ''))[:10]
            if date not in daily_activity:
                daily_activity[date] = {
                    'steps': [],
                    'calories': [],
                    'active_minutes': []
                }
            
            daily_activity[date]['steps'].append(record.get('steps', 0))
            daily_activity[date]['calories'].append(record.get('calories', 0))
            daily_activity[date]['active_minutes'].append(record.get('active_minutes', 0))
        
        # Analyze consistency
        avg_steps = [np.mean(day['steps']) for day in daily_activity.values()]
        step_consistency = np.std(avg_steps) / np.mean(avg_steps) if np.mean(avg_steps) > 0 else 1.0
        
        if step_consistency < 0.3:  # Consistent activity
            patterns.append({
                'pattern_type': 'behavioral',
                'pattern_name': 'consistent_activity_pattern',
                'description': 'Consistent daily activity pattern detected',
                'confidence_score': 0.8,
                'frequency': 'daily',
                'duration': 'ongoing',
                'pattern_data': {
                    'consistency_score': 1 - step_consistency,
                    'average_steps': np.mean(avg_steps),
                    'variation_coefficient': step_consistency
                },
                'detection_method': 'statistical_analysis',
                'data_sources': ['activity_data']
            })
        
        return patterns
    
    def _analyze_sleep_patterns(self, sleep_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sleep behavioral patterns."""
        patterns = []
        
        if len(sleep_data) < 7:
            return patterns
        
        # Calculate sleep metrics
        sleep_durations = [record.get('duration', 0) for record in sleep_data]
        sleep_qualities = [record.get('quality', 0) for record in sleep_data]
        
        avg_duration = np.mean(sleep_durations)
        avg_quality = np.mean(sleep_qualities)
        
        # Detect sleep pattern
        if avg_duration >= 7 and avg_duration <= 9 and avg_quality >= 7:
            pattern_name = 'optimal_sleep_pattern'
            description = 'Optimal sleep pattern detected'
            confidence = 0.9
        elif avg_duration < 6:
            pattern_name = 'insufficient_sleep_pattern'
            description = 'Insufficient sleep pattern detected'
            confidence = 0.8
        elif avg_quality < 5:
            pattern_name = 'poor_quality_sleep_pattern'
            description = 'Poor sleep quality pattern detected'
            confidence = 0.7
        else:
            pattern_name = 'suboptimal_sleep_pattern'
            description = 'Suboptimal sleep pattern detected'
            confidence = 0.6
        
        patterns.append({
            'pattern_type': 'behavioral',
            'pattern_name': pattern_name,
            'description': description,
            'confidence_score': confidence,
            'frequency': 'daily',
            'duration': 'ongoing',
            'pattern_data': {
                'average_duration': avg_duration,
                'average_quality': avg_quality,
                'sleep_efficiency': self._calculate_sleep_efficiency(sleep_data)
            },
            'detection_method': 'statistical_analysis',
            'data_sources': ['sleep_data']
        })
        
        return patterns
    
    def _calculate_sleep_efficiency(self, sleep_data: List[Dict[str, Any]]) -> float:
        """Calculate sleep efficiency."""
        if not sleep_data:
            return 0.0
        
        total_efficiency = 0
        count = 0
        
        for record in sleep_data:
            duration = record.get('duration', 0)
            time_in_bed = record.get('time_in_bed', duration)
            
            if time_in_bed > 0:
                efficiency = duration / time_in_bed
                total_efficiency += efficiency
                count += 1
        
        return total_efficiency / count if count > 0 else 0.0
    
    def _analyze_nutrition_patterns(self, nutrition_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze nutrition behavioral patterns."""
        patterns = []
        
        if len(nutrition_data) < 7:
            return patterns
        
        # Calculate nutrition metrics
        calorie_intakes = [record.get('calories', 0) for record in nutrition_data]
        avg_calories = np.mean(calorie_intakes)
        
        # Detect nutrition pattern
        if 1800 <= avg_calories <= 2200:  # Reasonable range
            pattern_name = 'balanced_nutrition_pattern'
            description = 'Balanced nutrition pattern detected'
            confidence = 0.8
        elif avg_calories < 1200:
            pattern_name = 'low_calorie_nutrition_pattern'
            description = 'Low calorie nutrition pattern detected'
            confidence = 0.7
        elif avg_calories > 2500:
            pattern_name = 'high_calorie_nutrition_pattern'
            description = 'High calorie nutrition pattern detected'
            confidence = 0.7
        else:
            pattern_name = 'moderate_nutrition_pattern'
            description = 'Moderate nutrition pattern detected'
            confidence = 0.6
        
        patterns.append({
            'pattern_type': 'behavioral',
            'pattern_name': pattern_name,
            'description': description,
            'confidence_score': confidence,
            'frequency': 'daily',
            'duration': 'ongoing',
            'pattern_data': {
                'average_calories': avg_calories,
                'calorie_variation': np.std(calorie_intakes)
            },
            'detection_method': 'statistical_analysis',
            'data_sources': ['nutrition_data']
        })
        
        return patterns
    
    async def _detect_cyclic_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect cyclic patterns using advanced algorithms."""
        # Implementation for cyclic pattern detection
        return []
    
    async def _detect_seasonal_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect seasonal patterns in health data."""
        # Implementation for seasonal pattern detection
        return []
    
    async def _detect_correlation_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect correlation patterns between different metrics."""
        # Implementation for correlation pattern detection
        return []
    
    async def _detect_cluster_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect cluster patterns using machine learning."""
        # Implementation for cluster pattern detection
        return []
    
    async def _score_patterns(self, patterns: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score patterns based on confidence and significance."""
        for pattern in patterns:
            # Ensure confidence score is set
            if 'confidence_score' not in pattern:
                pattern['confidence_score'] = 0.5
            
            # Adjust confidence based on data quality
            data_quality = self._assess_data_quality(pattern.get('data_sources', []), data)
            pattern['confidence_score'] *= data_quality
        
        return patterns
    
    def _assess_data_quality(self, data_sources: List[str], data: Dict[str, Any]) -> float:
        """Assess quality of data sources."""
        quality_scores = {
            'vital_signs': 0.9,
            'activity_data': 0.8,
            'sleep_data': 0.8,
            'nutrition_data': 0.7,
            'medication_data': 0.9,
            'symptom_data': 0.6
        }
        
        if not data_sources:
            return 0.5
        
        total_quality = sum(quality_scores.get(source, 0.5) for source in data_sources)
        return total_quality / len(data_sources)
    
    def _rank_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank patterns by importance and confidence."""
        def get_pattern_score(pattern):
            confidence = pattern.get('confidence_score', 0.5)
            frequency_weight = {
                'daily': 1.0,
                'weekly': 0.8,
                'monthly': 0.6,
                'ongoing': 0.9
            }.get(pattern.get('frequency', 'ongoing'), 0.5)
            
            return confidence * frequency_weight
        
        return sorted(patterns, key=get_pattern_score, reverse=True)
    
    async def _save_patterns(self, patterns: List[Dict[str, Any]], patient_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Save patterns to database."""
        saved_patterns = []
        
        for pattern_data in patterns:
            try:
                # Create pattern record
                pattern_db = HealthPatternDB(
                    patient_id=patient_id,
                    pattern_type=pattern_data['pattern_type'],
                    pattern_name=pattern_data['pattern_name'],
                    description=pattern_data['description'],
                    pattern_data=pattern_data['pattern_data'],
                    confidence_score=pattern_data['confidence_score'],
                    frequency=pattern_data.get('frequency'),
                    duration=pattern_data.get('duration'),
                    data_sources=pattern_data.get('data_sources', []),
                    detection_method=pattern_data.get('detection_method', 'unknown')
                )
                
                db.add(pattern_db)
                await db.flush()
                
                saved_patterns.append(pattern_data)
                
            except Exception as e:
                self.logger.error(f"Failed to save pattern: {e}")
                continue
        
        await db.commit()
        return saved_patterns
    
    def _count_by_type(self, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count patterns by type."""
        counts = {}
        for pattern in patterns:
            pattern_type = pattern.get('pattern_type', 'unknown')
            counts[pattern_type] = counts.get(pattern_type, 0) + 1
        return counts
    
    def _calculate_average_confidence(self, patterns: List[Dict[str, Any]]) -> float:
        """Calculate average confidence score."""
        if not patterns:
            return 0.0
        
        total_confidence = sum(pattern.get('confidence_score', 0.0) for pattern in patterns)
        return total_confidence / len(patterns) 