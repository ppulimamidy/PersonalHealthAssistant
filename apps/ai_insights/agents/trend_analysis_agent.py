"""
Trend Analysis Agent
Advanced AI agent for analyzing health data trends and patterns over time.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import json
import numpy as np
from scipy import stats
from scipy.signal import find_peaks
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_insight_agent import BaseInsightAgent, AgentResult, AgentStatus, AgentPriority
from ..models import (
    InsightDB, InsightType, InsightSeverity, InsightStatus, InsightCategory,
    InsightCreate, InsightResponse
)
from common.utils.logging import get_logger


class TrendAnalysisAgent(BaseInsightAgent):
    """Advanced AI agent for analyzing health data trends."""
    
    def __init__(self):
        super().__init__(
            agent_name="trend_analysis",
            priority=AgentPriority.HIGH
        )
        
        # Trend analysis models and algorithms
        self.trend_models = self._initialize_trend_models()
        self.seasonality_detectors = self._initialize_seasonality_detectors()
        self.forecasting_models = self._initialize_forecasting_models()
        
        # Trend analysis configurations
        self.trend_configs = self._load_trend_configurations()
        self.thresholds = self._load_thresholds()
        self.interpretation_rules = self._load_interpretation_rules()
    
    def _get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return [
            "time_series_analysis",
            "trend_detection",
            "seasonality_analysis",
            "forecasting",
            "change_point_detection",
            "trend_classification",
            "velocity_analysis",
            "acceleration_analysis",
            "multi_variate_trends",
            "trend_confidence_scoring"
        ]
    
    def _get_data_requirements(self) -> List[str]:
        """Get list of required data sources."""
        return [
            "patient_id",
            "vital_signs",
            "health_metrics",
            "lab_results",
            "medication_data",
            "lifestyle_data"
        ]
    
    def _get_output_schema(self) -> Dict[str, Any]:
        """Get output schema for the agent."""
        return {
            "trends": [
                {
                    "metric": "string",
                    "trend_type": "string",
                    "direction": "string",
                    "magnitude": "float",
                    "velocity": "float",
                    "acceleration": "float",
                    "confidence": "float",
                    "significance": "float",
                    "seasonality": "object",
                    "forecast": "object",
                    "change_points": "array"
                }
            ],
            "metadata": {
                "total_trends": "integer",
                "trends_by_type": "object",
                "trends_by_direction": "object",
                "average_confidence": "float",
                "analysis_timestamp": "string"
            }
        }
    
    async def execute(self, data: Dict[str, Any], db: AsyncSession) -> AgentResult:
        """
        Execute trend analysis.
        
        Args:
            data: Input health data
            db: Database session
            
        Returns:
            AgentResult: Trend analysis results
        """
        self.start_time = datetime.utcnow()
        self.status = AgentStatus.RUNNING
        
        try:
            self.logger.info(f"🚀 Starting trend analysis for patient {data.get('patient_id')}")
            
            # Preprocess data
            processed_data = await self.preprocess_data(data)
            
            # Analyze trends for different metrics
            trends = await self._analyze_trends(processed_data)
            
            # Detect seasonality patterns
            seasonal_trends = await self._detect_seasonality(trends, processed_data)
            
            # Perform forecasting
            forecasted_trends = await self._forecast_trends(seasonal_trends, processed_data)
            
            # Detect change points
            trends_with_changes = await self._detect_change_points(forecasted_trends, processed_data)
            
            # Classify and score trends
            classified_trends = self._classify_trends(trends_with_changes)
            
            # Generate insights from trends
            insights = await self._generate_trend_insights(classified_trends, processed_data)
            
            # Save trends to database
            saved_trends = await self._save_trends(classified_trends, data['patient_id'], db)
            
            # Update status
            self.status = AgentStatus.COMPLETED
            self.end_time = datetime.utcnow()
            
            # Create result
            result = AgentResult(
                success=True,
                agent_name=self.agent_name,
                status=AgentStatus.COMPLETED,
                trends=classified_trends,
                insights=insights,
                data={
                    'total_trends': len(classified_trends),
                    'trends_by_type': self._count_by_type(classified_trends),
                    'trends_by_direction': self._count_by_direction(classified_trends),
                    'average_confidence': self._calculate_average_confidence(classified_trends),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Postprocess results
            result = await self.postprocess_results(result)
            
            self.logger.info(f"✅ Trend analysis completed: {len(classified_trends)} trends analyzed")
            return result
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.end_time = datetime.utcnow()
            
            self.logger.error(f"❌ Trend analysis failed: {str(e)}")
            
            return AgentResult(
                success=False,
                agent_name=self.agent_name,
                status=AgentStatus.FAILED,
                error=str(e)
            )
    
    def _initialize_trend_models(self) -> Dict[str, Any]:
        """Initialize trend analysis models."""
        return {
            "linear_trend": self._create_linear_trend_model(),
            "polynomial_trend": self._create_polynomial_trend_model(),
            "exponential_trend": self._create_exponential_trend_model(),
            "logarithmic_trend": self._create_logarithmic_trend_model(),
            "moving_average": self._create_moving_average_model()
        }
    
    def _create_linear_trend_model(self) -> Dict[str, Any]:
        """Create linear trend analysis model."""
        return {
            "type": "linear_regression",
            "algorithm": "least_squares",
            "parameters": {
                "min_data_points": 3,
                "confidence_level": 0.95,
                "outlier_threshold": 2.0
            }
        }
    
    def _create_polynomial_trend_model(self) -> Dict[str, Any]:
        """Create polynomial trend analysis model."""
        return {
            "type": "polynomial_regression",
            "algorithm": "polyfit",
            "parameters": {
                "max_degree": 3,
                "min_data_points": 5,
                "cross_validation": True
            }
        }
    
    def _create_exponential_trend_model(self) -> Dict[str, Any]:
        """Create exponential trend analysis model."""
        return {
            "type": "exponential_regression",
            "algorithm": "curve_fit",
            "parameters": {
                "min_data_points": 4,
                "initial_guess": [1.0, 0.1],
                "bounds": ([0, -10], [10, 10])
            }
        }
    
    def _create_logarithmic_trend_model(self) -> Dict[str, Any]:
        """Create logarithmic trend analysis model."""
        return {
            "type": "logarithmic_regression",
            "algorithm": "curve_fit",
            "parameters": {
                "min_data_points": 4,
                "initial_guess": [1.0, 0.0],
                "bounds": ([0, -10], [10, 10])
            }
        }
    
    def _create_moving_average_model(self) -> Dict[str, Any]:
        """Create moving average model."""
        return {
            "type": "moving_average",
            "algorithm": "weighted_average",
            "parameters": {
                "window_sizes": [3, 7, 14, 30],
                "weights": "exponential",
                "min_data_points": 3
            }
        }
    
    def _initialize_seasonality_detectors(self) -> Dict[str, Any]:
        """Initialize seasonality detection models."""
        return {
            "fourier_analysis": self._create_fourier_analyzer(),
            "autocorrelation": self._create_autocorrelation_analyzer(),
            "seasonal_decomposition": self._create_seasonal_decomposer()
        }
    
    def _create_fourier_analyzer(self) -> Dict[str, Any]:
        """Create Fourier analysis for seasonality detection."""
        return {
            "type": "fourier_transform",
            "algorithm": "fft",
            "parameters": {
                "min_period": 2,
                "max_period": 365,
                "significance_threshold": 0.05
            }
        }
    
    def _create_autocorrelation_analyzer(self) -> Dict[str, Any]:
        """Create autocorrelation analysis."""
        return {
            "type": "autocorrelation",
            "algorithm": "pearson",
            "parameters": {
                "max_lag": 30,
                "confidence_interval": 0.95,
                "min_correlation": 0.3
            }
        }
    
    def _create_seasonal_decomposer(self) -> Dict[str, Any]:
        """Create seasonal decomposition model."""
        return {
            "type": "seasonal_decomposition",
            "algorithm": "stl",
            "parameters": {
                "period": "auto",
                "seasonal_window": 7,
                "trend_window": 15
            }
        }
    
    def _initialize_forecasting_models(self) -> Dict[str, Any]:
        """Initialize forecasting models."""
        return {
            "arima": self._create_arima_model(),
            "exponential_smoothing": self._create_exponential_smoothing_model(),
            "prophet": self._create_prophet_model()
        }
    
    def _create_arima_model(self) -> Dict[str, Any]:
        """Create ARIMA forecasting model."""
        return {
            "type": "arima",
            "algorithm": "auto_arima",
            "parameters": {
                "max_p": 5,
                "max_d": 2,
                "max_q": 5,
                "seasonal": True,
                "stepwise": True
            }
        }
    
    def _create_exponential_smoothing_model(self) -> Dict[str, Any]:
        """Create exponential smoothing model."""
        return {
            "type": "exponential_smoothing",
            "algorithm": "holt_winters",
            "parameters": {
                "seasonal_periods": 7,
                "trend": "add",
                "seasonal": "add",
                "damped": True
            }
        }
    
    def _create_prophet_model(self) -> Dict[str, Any]:
        """Create Prophet forecasting model."""
        return {
            "type": "prophet",
            "algorithm": "bayesian",
            "parameters": {
                "changepoint_prior_scale": 0.05,
                "seasonality_prior_scale": 10.0,
                "holidays_prior_scale": 10.0
            }
        }
    
    def _load_trend_configurations(self) -> Dict[str, Any]:
        """Load trend analysis configurations."""
        return {
            "vital_signs": {
                "heart_rate": {"min_data_points": 5, "trend_threshold": 0.1},
                "blood_pressure": {"min_data_points": 5, "trend_threshold": 0.05},
                "temperature": {"min_data_points": 3, "trend_threshold": 0.2},
                "oxygen_saturation": {"min_data_points": 3, "trend_threshold": 0.02}
            },
            "lab_results": {
                "glucose": {"min_data_points": 3, "trend_threshold": 0.1},
                "cholesterol": {"min_data_points": 2, "trend_threshold": 0.05},
                "creatinine": {"min_data_points": 2, "trend_threshold": 0.1}
            },
            "lifestyle": {
                "steps": {"min_data_points": 7, "trend_threshold": 0.2},
                "sleep_hours": {"min_data_points": 7, "trend_threshold": 0.3},
                "calories_burned": {"min_data_points": 7, "trend_threshold": 0.2}
            }
        }
    
    def _load_thresholds(self) -> Dict[str, Any]:
        """Load trend analysis thresholds."""
        return {
            "significance_level": 0.05,
            "confidence_threshold": 0.7,
            "magnitude_threshold": 0.1,
            "velocity_threshold": 0.05,
            "acceleration_threshold": 0.02
        }
    
    def _load_interpretation_rules(self) -> Dict[str, Any]:
        """Load trend interpretation rules."""
        return {
            "improving": {
                "description": "Metric is showing positive improvement",
                "severity": InsightSeverity.LOW,
                "confidence_boost": 0.1
            },
            "stable": {
                "description": "Metric is maintaining stable levels",
                "severity": InsightSeverity.LOW,
                "confidence_boost": 0.05
            },
            "declining": {
                "description": "Metric is showing concerning decline",
                "severity": InsightSeverity.MEDIUM,
                "confidence_boost": 0.15
            },
            "fluctuating": {
                "description": "Metric is showing irregular fluctuations",
                "severity": InsightSeverity.MEDIUM,
                "confidence_boost": 0.1
            }
        }
    
    async def _analyze_trends(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze trends for all available metrics."""
        trends = []
        
        # Analyze vital signs trends
        if 'vital_signs' in data:
            vital_trends = await self._analyze_vital_signs_trends(data['vital_signs'])
            trends.extend(vital_trends)
        
        # Analyze lab results trends
        if 'lab_results' in data:
            lab_trends = await self._analyze_lab_results_trends(data['lab_results'])
            trends.extend(lab_trends)
        
        # Analyze lifestyle trends
        if 'lifestyle_data' in data:
            lifestyle_trends = await self._analyze_lifestyle_trends(data['lifestyle_data'])
            trends.extend(lifestyle_trends)
        
        return trends
    
    async def _analyze_vital_signs_trends(self, vital_signs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in vital signs data."""
        trends = []
        
        # Group by metric type
        metrics = {}
        for record in vital_signs:
            metric_type = record.get('metric_type')
            if metric_type not in metrics:
                metrics[metric_type] = []
            metrics[metric_type].append(record)
        
        # Analyze each metric
        for metric_type, records in metrics.items():
            if len(records) < 3:  # Need minimum data points
                continue
                
            # Sort by timestamp
            sorted_records = sorted(records, key=lambda x: x.get('timestamp', ''))
            
            # Extract values and timestamps
            values = [float(r.get('value', 0)) for r in sorted_records]
            timestamps = [r.get('timestamp', '') for r in sorted_records]
            
            # Analyze trend
            trend = await self._calculate_trend(metric_type, values, timestamps)
            if trend:
                trends.append(trend)
        
        return trends
    
    async def _analyze_lab_results_trends(self, lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in lab results data."""
        trends = []
        
        # Group by test type
        tests = {}
        for record in lab_results:
            test_type = record.get('test_type')
            if test_type not in tests:
                tests[test_type] = []
            tests[test_type].append(record)
        
        # Analyze each test type
        for test_type, records in tests.items():
            if len(records) < 2:  # Need minimum data points
                continue
                
            # Sort by date
            sorted_records = sorted(records, key=lambda x: x.get('test_date', ''))
            
            # Extract values and dates
            values = [float(r.get('value', 0)) for r in sorted_records]
            dates = [r.get('test_date', '') for r in sorted_records]
            
            # Analyze trend
            trend = await self._calculate_trend(test_type, values, dates)
            if trend:
                trends.append(trend)
        
        return trends
    
    async def _analyze_lifestyle_trends(self, lifestyle_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trends in lifestyle data."""
        trends = []
        
        # Group by activity type
        activities = {}
        for record in lifestyle_data:
            activity_type = record.get('activity_type')
            if activity_type not in activities:
                activities[activity_type] = []
            activities[activity_type].append(record)
        
        # Analyze each activity type
        for activity_type, records in activities.items():
            if len(records) < 7:  # Need more data points for lifestyle
                continue
                
            # Sort by date
            sorted_records = sorted(records, key=lambda x: x.get('date', ''))
            
            # Extract values and dates
            values = [float(r.get('value', 0)) for r in sorted_records]
            dates = [r.get('date', '') for r in sorted_records]
            
            # Analyze trend
            trend = await self._calculate_trend(activity_type, values, dates)
            if trend:
                trends.append(trend)
        
        return trends
    
    async def _calculate_trend(self, metric: str, values: List[float], timestamps: List[str]) -> Optional[Dict[str, Any]]:
        """Calculate trend for a specific metric."""
        if len(values) < 3:
            return None
        
        try:
            # Convert timestamps to numeric indices
            x = np.arange(len(values))
            y = np.array(values)
            
            # Fit linear trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Calculate trend characteristics
            trend_magnitude = abs(slope)
            trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            confidence = r_value ** 2  # R-squared value
            significance = 1 - p_value
            
            # Calculate velocity (rate of change)
            velocity = slope
            
            # Calculate acceleration (change in velocity)
            if len(values) >= 4:
                # Use second derivative approximation
                acceleration = np.polyfit(x, y, 2)[0] * 2
            else:
                acceleration = 0.0
            
            # Determine trend type
            trend_type = self._classify_trend_type(slope, r_value, p_value)
            
            # Check if trend meets significance threshold
            if p_value > self.thresholds['significance_level']:
                return None
            
            return {
                "metric": metric,
                "trend_type": trend_type,
                "direction": trend_direction,
                "magnitude": trend_magnitude,
                "velocity": velocity,
                "acceleration": acceleration,
                "confidence": confidence,
                "significance": significance,
                "data_points": len(values),
                "time_span": len(values),
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_value ** 2,
                "p_value": p_value,
                "std_error": std_err
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating trend for {metric}: {e}")
            return None
    
    def _classify_trend_type(self, slope: float, r_value: float, p_value: float) -> str:
        """Classify the type of trend."""
        if p_value > self.thresholds['significance_level']:
            return "no_trend"
        
        if abs(slope) < self.thresholds['magnitude_threshold']:
            return "stable"
        
        if r_value ** 2 > 0.8:
            if abs(slope) > self.thresholds['magnitude_threshold'] * 2:
                return "strong_trend"
            else:
                return "moderate_trend"
        else:
            return "weak_trend"
    
    async def _detect_seasonality(self, trends: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect seasonality patterns in trends."""
        for trend in trends:
            metric = trend['metric']
            
            # Get time series data for the metric
            time_series = self._extract_time_series(metric, data)
            if not time_series or len(time_series) < 7:
                continue
            
            # Detect seasonality
            seasonality = await self._analyze_seasonality(time_series)
            if seasonality:
                trend['seasonality'] = seasonality
        
        return trends
    
    def _extract_time_series(self, metric: str, data: Dict[str, Any]) -> Optional[List[float]]:
        """Extract time series data for a specific metric."""
        # This is a simplified implementation
        # In a real scenario, you'd extract the actual time series data
        return None
    
    async def _analyze_seasonality(self, time_series: List[float]) -> Optional[Dict[str, Any]]:
        """Analyze seasonality in time series data."""
        if not time_series or len(time_series) < 7:
            return None
        
        try:
            # Simple seasonality detection using autocorrelation
            autocorr = np.correlate(time_series, time_series, mode='full')
            autocorr = autocorr[len(time_series)-1:]
            
            # Find peaks in autocorrelation
            peaks, _ = find_peaks(autocorr[:len(autocorr)//2])
            
            if len(peaks) > 0:
                # Find the most significant period
                main_period = peaks[np.argmax(autocorr[peaks])]
                
                return {
                    "has_seasonality": True,
                    "main_period": int(main_period),
                    "seasonality_strength": float(autocorr[main_period] / autocorr[0]),
                    "detection_method": "autocorrelation"
                }
            else:
                return {
                    "has_seasonality": False,
                    "detection_method": "autocorrelation"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing seasonality: {e}")
            return None
    
    async def _forecast_trends(self, trends: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Forecast future values for trends."""
        for trend in trends:
            metric = trend['metric']
            
            # Get time series data for the metric
            time_series = self._extract_time_series(metric, data)
            if not time_series or len(time_series) < 5:
                continue
            
            # Generate forecast
            forecast = await self._generate_forecast(time_series, trend)
            if forecast:
                trend['forecast'] = forecast
        
        return trends
    
    async def _generate_forecast(self, time_series: List[float], trend: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate forecast for a time series."""
        if not time_series or len(time_series) < 5:
            return None
        
        try:
            # Simple linear forecast based on trend
            slope = trend.get('slope', 0)
            intercept = trend.get('intercept', 0)
            
            # Forecast next 7 days
            forecast_days = 7
            forecast_values = []
            
            for i in range(1, forecast_days + 1):
                future_x = len(time_series) + i
                forecast_value = slope * future_x + intercept
                forecast_values.append(forecast_value)
            
            return {
                "forecast_values": forecast_values,
                "forecast_days": forecast_days,
                "confidence_interval": [0.8, 1.2],  # Simplified
                "method": "linear_extrapolation"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating forecast: {e}")
            return None
    
    async def _detect_change_points(self, trends: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect change points in trends."""
        for trend in trends:
            metric = trend['metric']
            
            # Get time series data for the metric
            time_series = self._extract_time_series(metric, data)
            if not time_series or len(time_series) < 10:
                continue
            
            # Detect change points
            change_points = await self._find_change_points(time_series)
            if change_points:
                trend['change_points'] = change_points
        
        return trends
    
    async def _find_change_points(self, time_series: List[float]) -> List[Dict[str, Any]]:
        """Find change points in time series data."""
        if not time_series or len(time_series) < 10:
            return []
        
        try:
            # Simple change point detection using rolling statistics
            window_size = min(5, len(time_series) // 2)
            change_points = []
            
            for i in range(window_size, len(time_series) - window_size):
                # Calculate statistics for windows before and after
                before_window = time_series[i-window_size:i]
                after_window = time_series[i:i+window_size]
                
                before_mean = np.mean(before_window)
                after_mean = np.mean(after_window)
                
                # Check if there's a significant change
                change_magnitude = abs(after_mean - before_mean) / (before_mean + 1e-8)
                
                if change_magnitude > 0.2:  # 20% change threshold
                    change_points.append({
                        "index": i,
                        "timestamp": f"point_{i}",
                        "change_magnitude": change_magnitude,
                        "before_mean": before_mean,
                        "after_mean": after_mean,
                        "change_type": "mean_shift"
                    })
            
            return change_points
            
        except Exception as e:
            self.logger.error(f"❌ Error finding change points: {e}")
            return []
    
    def _classify_trends(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify and score trends."""
        for trend in trends:
            # Add trend classification
            trend['classification'] = self._get_trend_classification(trend)
            
            # Add severity assessment
            trend['severity'] = self._assess_trend_severity(trend)
            
            # Add interpretation
            trend['interpretation'] = self._get_trend_interpretation(trend)
        
        return trends
    
    def _get_trend_classification(self, trend: Dict[str, Any]) -> str:
        """Get trend classification."""
        direction = trend.get('direction', 'stable')
        magnitude = trend.get('magnitude', 0)
        confidence = trend.get('confidence', 0)
        
        if confidence < 0.5:
            return "uncertain"
        elif magnitude < self.thresholds['magnitude_threshold']:
            return "minimal"
        elif direction == "increasing":
            return "improving"
        elif direction == "decreasing":
            return "declining"
        else:
            return "stable"
    
    def _assess_trend_severity(self, trend: Dict[str, Any]) -> InsightSeverity:
        """Assess severity of a trend."""
        magnitude = trend.get('magnitude', 0)
        velocity = abs(trend.get('velocity', 0))
        confidence = trend.get('confidence', 0)
        
        # High severity if high magnitude, high velocity, and high confidence
        if magnitude > self.thresholds['magnitude_threshold'] * 3 and velocity > self.thresholds['velocity_threshold'] * 2 and confidence > 0.8:
            return InsightSeverity.HIGH
        elif magnitude > self.thresholds['magnitude_threshold'] * 2 and velocity > self.thresholds['velocity_threshold'] and confidence > 0.7:
            return InsightSeverity.MEDIUM
        else:
            return InsightSeverity.LOW
    
    def _get_trend_interpretation(self, trend: Dict[str, Any]) -> str:
        """Get human-readable interpretation of trend."""
        metric = trend.get('metric', '')
        direction = trend.get('direction', 'stable')
        magnitude = trend.get('magnitude', 0)
        classification = trend.get('classification', '')
        
        interpretations = {
            'improving': f"{metric} is showing {classification} improvement",
            'declining': f"{metric} is showing {classification} decline",
            'stable': f"{metric} is maintaining stable levels",
            'minimal': f"{metric} shows minimal change",
            'uncertain': f"{metric} trend is uncertain due to limited data"
        }
        
        return interpretations.get(classification, f"{metric} trend analysis completed")
    
    async def _generate_trend_insights(self, trends: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from trend analysis."""
        insights = []
        
        for trend in trends:
            if trend.get('severity') in [InsightSeverity.MEDIUM, InsightSeverity.HIGH]:
                insight = await self._create_trend_insight(trend, data)
                if insight:
                    insights.append(insight)
        
        return insights
    
    async def _create_trend_insight(self, trend: Dict[str, Any], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an insight from a trend."""
        metric = trend.get('metric', '')
        direction = trend.get('direction', 'stable')
        magnitude = trend.get('magnitude', 0)
        confidence = trend.get('confidence', 0)
        severity = trend.get('severity', InsightSeverity.LOW)
        interpretation = trend.get('interpretation', '')
        
        # Determine insight type based on trend characteristics
        if direction == "increasing":
            insight_type = InsightType.TREND_ANALYSIS
            category = InsightCategory.HEALTH_METRICS
        elif direction == "decreasing":
            insight_type = InsightType.RISK_ASSESSMENT
            category = InsightCategory.CLINICAL
        else:
            insight_type = InsightType.TREND_ANALYSIS
            category = InsightCategory.HEALTH_METRICS
        
        # Create insight title
        title = f"{metric.title()} Trend Analysis"
        
        # Create insight description
        description = f"{interpretation}. The trend shows a {direction} pattern with {magnitude:.2f} magnitude and {confidence:.1%} confidence."
        
        # Add recommendations if severity is high
        recommendations = []
        if severity == InsightSeverity.HIGH:
            if direction == "decreasing":
                recommendations.append({
                    "type": "monitoring",
                    "description": f"Monitor {metric} closely and consider intervention",
                    "priority": "high"
                })
            elif direction == "increasing":
                recommendations.append({
                    "type": "positive_reinforcement",
                    "description": f"Continue current practices that are improving {metric}",
                    "priority": "medium"
                })
        
        return {
            "insight_type": insight_type,
            "category": category,
            "title": title,
            "description": description,
            "severity": severity,
            "confidence_score": confidence,
            "relevance_score": min(confidence + 0.1, 1.0),
            "supporting_evidence": {
                "trend_data": trend,
                "data_sources": ["trend_analysis"],
                "analysis_method": "statistical_trend_analysis"
            },
            "recommendations": recommendations
        }
    
    async def _save_trends(self, trends: List[Dict[str, Any]], patient_id: UUID, db: AsyncSession) -> List[Dict[str, Any]]:
        """Save trends to database."""
        saved_trends = []
        
        for trend in trends:
            try:
                # Create insight record for significant trends
                if trend.get('severity') in [InsightSeverity.MEDIUM, InsightSeverity.HIGH]:
                    insight_data = InsightCreate(
                        patient_id=patient_id,
                        insight_type=InsightType.TREND_ANALYSIS,
                        category=InsightCategory.HEALTH_METRICS,
                        title=trend.get('interpretation', 'Trend Analysis'),
                        description=f"Trend analysis for {trend.get('metric', '')}: {trend.get('interpretation', '')}",
                        severity=trend.get('severity', InsightSeverity.LOW),
                        confidence_score=trend.get('confidence', 0.0),
                        relevance_score=min(trend.get('confidence', 0.0) + 0.1, 1.0),
                        supporting_evidence=trend,
                        data_sources=["trend_analysis"]
                    )
                    
                    insight_db = InsightDB(**insight_data.dict())
                    db.add(insight_db)
                    await db.flush()
                    await db.refresh(insight_db)
                    
                    saved_trends.append(InsightResponse.from_orm(insight_db))
                
            except Exception as e:
                self.logger.error(f"❌ Error saving trend {trend.get('metric', '')}: {e}")
                continue
        
        await db.commit()
        return saved_trends
    
    def _count_by_type(self, trends: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count trends by type."""
        counts = {}
        for trend in trends:
            trend_type = trend.get('trend_type', 'unknown')
            counts[trend_type] = counts.get(trend_type, 0) + 1
        return counts
    
    def _count_by_direction(self, trends: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count trends by direction."""
        counts = {}
        for trend in trends:
            direction = trend.get('direction', 'unknown')
            counts[direction] = counts.get(direction, 0) + 1
        return counts
    
    def _calculate_average_confidence(self, trends: List[Dict[str, Any]]) -> float:
        """Calculate average confidence score."""
        if not trends:
            return 0.0
        
        confidences = [trend.get('confidence', 0.0) for trend in trends]
        return sum(confidences) / len(confidences) 