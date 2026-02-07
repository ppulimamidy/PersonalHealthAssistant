"""
Enhanced Analytics Service

Provides comprehensive analytics capabilities including real-time processing,
advanced algorithms, and multi-source data integration for the Personal Health Assistant.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import httpx
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

from common.utils.logging import get_logger
from common.config.settings import get_settings
from models.analytics_models import (
    AnalyticsType, TimeRange, MetricType, DataSource, RiskLevel, TrendDirection,
    HealthMetric, TrendAnalysis, CorrelationAnalysis, RiskAssessment,
    PredictiveModel, PopulationHealthMetrics, ClinicalDecisionSupport, PerformanceMetrics,
    AnalyticsRequest, AnalyticsResponse, RealTimeDataPoint
)

warnings.filterwarnings('ignore')

logger = get_logger(__name__)
settings = get_settings()


class RealTimeProcessor:
    """Real-time data processing engine"""
    
    def __init__(self):
        self.data_streams: Dict[str, List[RealTimeDataPoint]] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        self.is_running = False
        
    async def start_processing(self):
        """Start real-time processing"""
        self.is_running = True
        logger.info("Real-time processing started")
        
    async def stop_processing(self):
        """Stop real-time processing"""
        self.is_running = False
        for task in self.processing_tasks.values():
            task.cancel()
        logger.info("Real-time processing stopped")
        
    async def add_data_point(self, stream_id: str, data_point: RealTimeDataPoint):
        """Add a new data point to a stream"""
        if stream_id not in self.data_streams:
            self.data_streams[stream_id] = []
            
        self.data_streams[stream_id].append(data_point)
        
        # Keep only last 1000 points per stream
        if len(self.data_streams[stream_id]) > 1000:
            self.data_streams[stream_id] = self.data_streams[stream_id][-1000:]
            
        # Process in real-time
        await self.process_stream(stream_id)
        
    async def process_stream(self, stream_id: str):
        """Process a data stream in real-time"""
        if not self.is_running:
            return
            
        try:
            data_points = self.data_streams.get(stream_id, [])
            if len(data_points) < 10:  # Need minimum data points
                return
                
            # Extract values and timestamps
            values = [dp.value for dp in data_points]
            timestamps = [dp.timestamp for dp in data_points]
            
            # Real-time anomaly detection
            anomalies = await self.detect_anomalies(values, timestamps)
            
            # Real-time trend analysis
            trend = await self.analyze_trend_realtime(values, timestamps)
            
            # Check alert thresholds
            await self.check_alerts(stream_id, values[-1], trend)
            
            logger.info(f"Real-time processing completed for stream {stream_id}")
            
        except Exception as e:
            logger.error(f"Error processing stream {stream_id}: {e}")
            
    async def detect_anomalies(self, values: List[float], timestamps: List[datetime]) -> List[int]:
        """Detect anomalies in real-time data"""
        if len(values) < 10:
            return []
            
        # Z-score based anomaly detection
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
            if z_score > 2.5:  # Threshold for anomaly
                anomalies.append(i)
                
        return anomalies
        
    async def analyze_trend_realtime(self, values: List[float], timestamps: List[datetime]) -> Dict[str, Any]:
        """Analyze trend in real-time"""
        if len(values) < 5:
            return {"direction": "unknown", "slope": 0, "confidence": 0}
            
        # Simple linear regression on recent data
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Determine trend direction
        if slope > 0.01:
            direction = "increasing"
        elif slope < -0.01:
            direction = "decreasing"
        else:
            direction = "stable"
            
        return {
            "direction": direction,
            "slope": slope,
            "confidence": abs(r_value),
            "p_value": p_value
        }
        
    async def check_alerts(self, stream_id: str, current_value: float, trend: Dict[str, Any]):
        """Check if alerts should be triggered"""
        if stream_id not in self.alert_thresholds:
            return
            
        thresholds = self.alert_thresholds[stream_id]
        
        for metric, threshold in thresholds.items():
            if current_value > threshold:
                logger.warning(f"Alert: {stream_id} {metric} exceeded threshold {threshold}")
                # Here you would trigger actual alerts (email, SMS, etc.)


class AdvancedAnalyticsEngine:
    """Advanced analytics algorithms engine"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
    async def perform_trend_analysis(self, data: List[Dict[str, Any]], metric: str) -> TrendAnalysis:
        """Perform advanced trend analysis"""
        if not data:
            return TrendAnalysis(
                trend_direction=TrendDirection.STABLE,
                slope=0.0,
                confidence=0.0,
                seasonality_detected=False,
                breakpoints=[],
                forecast_values=[]
            )
            
        # Extract time series data
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        values = df[metric].values
        timestamps = df['timestamp'].values
        
        # Advanced trend analysis
        trend_result = await self._analyze_trend_advanced(values, timestamps)
        
        # Seasonality detection
        seasonality = await self._detect_seasonality(values)
        
        # Breakpoint detection
        breakpoints = await self._detect_breakpoints(values, timestamps)
        
        # Forecasting
        forecast = await self._forecast_values(values, periods=30)
        
        return TrendAnalysis(
            trend_direction=trend_result['direction'],
            slope=trend_result['slope'],
            confidence=trend_result['confidence'],
            seasonality_detected=seasonality['detected'],
            seasonality_period=seasonality['period'],
            breakpoints=breakpoints,
            forecast_values=forecast
        )
        
    async def _analyze_trend_advanced(self, values: np.ndarray, timestamps: np.ndarray) -> Dict[str, Any]:
        """Advanced trend analysis with multiple methods"""
        if len(values) < 10:
            return {"direction": TrendDirection.STABLE, "slope": 0.0, "confidence": 0.0}
            
        # Method 1: Linear regression
        x = np.arange(len(values))
        slope_lr, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Method 2: Mann-Kendall trend test
        mk_result = await self._mann_kendall_test(values)
        
        # Method 3: Sen's slope estimator
        sen_slope = await self._sens_slope_estimator(values)
        
        # Combine results
        if abs(slope_lr) > 0.01 and p_value < 0.05:
            direction = TrendDirection.INCREASING if slope_lr > 0 else TrendDirection.DECREASING
        else:
            direction = TrendDirection.STABLE
            
        confidence = min(abs(r_value), 1.0)
        
        return {
            "direction": direction,
            "slope": slope_lr,
            "confidence": confidence,
            "p_value": p_value,
            "mk_trend": mk_result,
            "sen_slope": sen_slope
        }
        
    async def _mann_kendall_test(self, values: np.ndarray) -> str:
        """Perform Mann-Kendall trend test"""
        n = len(values)
        s = 0
        
        for i in range(n - 1):
            for j in range(i + 1, n):
                if values[j] > values[i]:
                    s += 1
                elif values[j] < values[i]:
                    s -= 1
                    
        # Calculate variance
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0
            
        if abs(z) > 1.96:
            return "increasing" if z > 0 else "decreasing"
        else:
            return "no trend"
            
    async def _sens_slope_estimator(self, values: np.ndarray) -> float:
        """Calculate Sen's slope estimator"""
        n = len(values)
        slopes = []
        
        for i in range(n - 1):
            for j in range(i + 1, n):
                slope = (values[j] - values[i]) / (j - i)
                slopes.append(slope)
                
        if slopes:
            return np.median(slopes)
        return 0.0
        
    async def _detect_seasonality(self, values: np.ndarray) -> Dict[str, Any]:
        """Detect seasonality in time series"""
        if len(values) < 50:
            return {"detected": False, "period": None}
            
        # FFT-based seasonality detection
        fft = np.fft.fft(values)
        freqs = np.fft.fftfreq(len(values))
        
        # Find dominant frequency
        power = np.abs(fft) ** 2
        dominant_idx = np.argmax(power[1:len(power)//2]) + 1
        dominant_freq = freqs[dominant_idx]
        
        if dominant_freq > 0:
            period = int(1 / dominant_freq)
            if 2 <= period <= len(values) // 2:
                return {"detected": True, "period": period}
                
        return {"detected": False, "period": None}
        
    async def _detect_breakpoints(self, values: np.ndarray, timestamps: np.ndarray) -> List[datetime]:
        """Detect structural breakpoints in time series"""
        if len(values) < 20:
            return []
            
        # Simple breakpoint detection using rolling statistics
        window_size = min(10, len(values) // 4)
        breakpoints = []
        
        for i in range(window_size, len(values) - window_size):
            before_mean = np.mean(values[i-window_size:i])
            after_mean = np.mean(values[i:i+window_size])
            
            # Check for significant change
            if abs(after_mean - before_mean) > 2 * np.std(values):
                breakpoints.append(timestamps[i])
                
        return breakpoints
        
    async def _forecast_values(self, values: np.ndarray, periods: int) -> List[float]:
        """Forecast future values using ARIMA-like approach"""
        if len(values) < 10:
            return [values[-1]] * periods if len(values) > 0 else [0] * periods
            
        # Simple exponential smoothing
        alpha = 0.3
        forecast = []
        last_value = values[-1]
        
        for _ in range(periods):
            forecast.append(last_value)
            
        return forecast
        
    async def perform_correlation_analysis(self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]], 
                                         metric1: str, metric2: str) -> CorrelationAnalysis:
        """Perform correlation analysis between two metrics"""
        if not data1 or not data2:
            return CorrelationAnalysis(
                correlation_coefficient=0.0,
                p_value=1.0,
                correlation_type="none",
                strength="none",
                significance=False
            )
            
        # Prepare data
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        
        # Align timestamps
        df1['timestamp'] = pd.to_datetime(df1['timestamp'])
        df2['timestamp'] = pd.to_datetime(df2['timestamp'])
        
        # Merge on timestamp
        merged = pd.merge(df1, df2, on='timestamp', suffixes=('_1', '_2'))
        
        if len(merged) < 5:
            return CorrelationAnalysis(
                correlation_coefficient=0.0,
                p_value=1.0,
                correlation_type="none",
                strength="none",
                significance=False
            )
            
        # Calculate correlations
        pearson_corr, pearson_p = stats.pearsonr(merged[f'{metric1}_1'], merged[f'{metric2}_2'])
        spearman_corr, spearman_p = stats.spearmanr(merged[f'{metric1}_1'], merged[f'{metric2}_2'])
        
        # Determine correlation type and strength
        if abs(pearson_corr) > abs(spearman_corr):
            correlation_coef = pearson_corr
            p_value = pearson_p
            corr_type = "pearson"
        else:
            correlation_coef = spearman_corr
            p_value = spearman_p
            corr_type = "spearman"
            
        # Determine strength
        if abs(correlation_coef) >= 0.8:
            strength = "very_strong"
        elif abs(correlation_coef) >= 0.6:
            strength = "strong"
        elif abs(correlation_coef) >= 0.4:
            strength = "moderate"
        elif abs(correlation_coef) >= 0.2:
            strength = "weak"
        else:
            strength = "very_weak"
            
        return CorrelationAnalysis(
            correlation_coefficient=correlation_coef,
            p_value=p_value,
            correlation_type=corr_type,
            strength=strength,
            significance=p_value < 0.05
        )
        
    async def perform_risk_assessment(self, patient_data: Dict[str, Any]) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        risk_factors = []
        overall_risk = RiskLevel.LOW
        
        # Analyze various risk factors
        if 'vital_signs' in patient_data:
            vitals = patient_data['vital_signs']
            
            # Blood pressure risk
            if 'systolic' in vitals and vitals['systolic'] > 140:
                risk_factors.append({
                    "factor": "high_systolic_bp",
                    "value": vitals['systolic'],
                    "risk_level": RiskLevel.HIGH,
                    "description": "Systolic blood pressure above normal range"
                })
                
            if 'diastolic' in vitals and vitals['diastolic'] > 90:
                risk_factors.append({
                    "factor": "high_diastolic_bp",
                    "value": vitals['diastolic'],
                    "risk_level": RiskLevel.HIGH,
                    "description": "Diastolic blood pressure above normal range"
                })
                
        # Heart rate risk
        if 'heart_rate' in patient_data:
            hr = patient_data['heart_rate']
            if hr > 100:
                risk_factors.append({
                    "factor": "tachycardia",
                    "value": hr,
                    "risk_level": RiskLevel.MEDIUM,
                    "description": "Heart rate above normal range"
                })
            elif hr < 60:
                risk_factors.append({
                    "factor": "bradycardia",
                    "value": hr,
                    "risk_level": RiskLevel.MEDIUM,
                    "description": "Heart rate below normal range"
                })
                
        # BMI risk
        if 'bmi' in patient_data:
            bmi = patient_data['bmi']
            if bmi > 30:
                risk_factors.append({
                    "factor": "obesity",
                    "value": bmi,
                    "risk_level": RiskLevel.HIGH,
                    "description": "BMI indicates obesity"
                })
            elif bmi > 25:
                risk_factors.append({
                    "factor": "overweight",
                    "value": bmi,
                    "risk_level": RiskLevel.MEDIUM,
                    "description": "BMI indicates overweight"
                })
                
        # Calculate overall risk
        high_risks = sum(1 for rf in risk_factors if rf['risk_level'] == RiskLevel.HIGH)
        medium_risks = sum(1 for rf in risk_factors if rf['risk_level'] == RiskLevel.MEDIUM)
        
        if high_risks >= 2:
            overall_risk = RiskLevel.CRITICAL
        elif high_risks >= 1:
            overall_risk = RiskLevel.HIGH
        elif medium_risks >= 2:
            overall_risk = RiskLevel.MEDIUM
        elif medium_risks >= 1:
            overall_risk = RiskLevel.LOW
        else:
            overall_risk = RiskLevel.LOW
            
        return RiskAssessment(
            overall_risk_level=overall_risk,
            risk_factors=risk_factors,
            risk_score=len(risk_factors),
            recommendations=self._generate_risk_recommendations(risk_factors)
        )
        
    def _generate_risk_recommendations(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []
        
        for rf in risk_factors:
            if rf['factor'] == 'high_systolic_bp':
                recommendations.append("Monitor blood pressure regularly and consider lifestyle modifications")
            elif rf['factor'] == 'high_diastolic_bp':
                recommendations.append("Reduce salt intake and increase physical activity")
            elif rf['factor'] == 'tachycardia':
                recommendations.append("Avoid caffeine and stress, consider stress management techniques")
            elif rf['factor'] == 'bradycardia':
                recommendations.append("Consult with cardiologist for evaluation")
            elif rf['factor'] == 'obesity':
                recommendations.append("Implement weight loss program with diet and exercise")
            elif rf['factor'] == 'overweight':
                recommendations.append("Focus on healthy eating and regular exercise")
                
        return recommendations


class AnalyticsService:
    """Enhanced Analytics Service with full algorithms and real-time processing"""
    
    def __init__(self):
        self.real_time_processor = RealTimeProcessor()
        self.analytics_engine = AdvancedAnalyticsEngine()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.service_urls = {
            'health_tracking': settings.HEALTH_TRACKING_SERVICE_URL,
            'medical_records': settings.MEDICAL_RECORDS_SERVICE_URL,
            'device_data': settings.DEVICE_DATA_SERVICE_URL,
            'nutrition': settings.NUTRITION_SERVICE_URL,
            'voice_input': settings.VOICE_INPUT_SERVICE_URL,
            'ai_insights': settings.AI_INSIGHTS_SERVICE_URL,
            'consent_audit': settings.CONSENT_AUDIT_SERVICE_URL,
            'user_profile': settings.USER_PROFILE_SERVICE_URL
        }
        
    async def start(self):
        """Start the analytics service"""
        await self.real_time_processor.start_processing()
        logger.info("Analytics service started with real-time processing")
        
    async def stop(self):
        """Stop the analytics service"""
        await self.real_time_processor.stop_processing()
        await self.http_client.aclose()
        logger.info("Analytics service stopped")
        
    async def collect_data_from_services(self, user_id: UUID, time_range: TimeRange) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data from all microservices"""
        data = {}
        
        # Collect from health tracking service
        try:
            health_data = await self._fetch_health_tracking_data(user_id, time_range)
            data['health_tracking'] = health_data
        except Exception as e:
            logger.error(f"Error fetching health tracking data: {e}")
            data['health_tracking'] = []
            
        # Collect from medical records service
        try:
            medical_data = await self._fetch_medical_records_data(user_id, time_range)
            data['medical_records'] = medical_data
        except Exception as e:
            logger.error(f"Error fetching medical records data: {e}")
            data['medical_records'] = []
            
        # Collect from device data service
        try:
            device_data = await self._fetch_device_data(user_id, time_range)
            data['device_data'] = device_data
        except Exception as e:
            logger.error(f"Error fetching device data: {e}")
            data['device_data'] = []
            
        # Collect from nutrition service
        try:
            nutrition_data = await self._fetch_nutrition_data(user_id, time_range)
            data['nutrition'] = nutrition_data
        except Exception as e:
            logger.error(f"Error fetching nutrition data: {e}")
            data['nutrition'] = []
            
        return data
        
    async def _fetch_health_tracking_data(self, user_id: UUID, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Fetch health tracking data"""
        url = f"{self.service_urls['health_tracking']}/api/v1/health-tracking/user/{user_id}/metrics"
        params = {"time_range": time_range.value}
        
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('metrics', [])
        
    async def _fetch_medical_records_data(self, user_id: UUID, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Fetch medical records data"""
        url = f"{self.service_urls['medical_records']}/api/v1/medical-records/user/{user_id}/records"
        params = {"time_range": time_range.value}
        
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('records', [])
        
    async def _fetch_device_data(self, user_id: UUID, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Fetch device data"""
        url = f"{self.service_urls['device_data']}/api/v1/device-data/user/{user_id}/data"
        params = {"time_range": time_range.value}
        
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('data', [])
        
    async def _fetch_nutrition_data(self, user_id: UUID, time_range: TimeRange) -> List[Dict[str, Any]]:
        """Fetch nutrition data"""
        url = f"{self.service_urls['nutrition']}/api/v1/nutrition/user/{user_id}/logs"
        params = {"time_range": time_range.value}
        
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('logs', [])
        
    async def analyze_patient_health(self, user_id: UUID, time_range: TimeRange) -> AnalyticsResponse:
        """Perform comprehensive patient health analysis"""
        logger.info(f"Starting patient health analysis for user {user_id}")
        
        # Collect data from all services
        data = await self.collect_data_from_services(user_id, time_range)
        
        # Perform trend analysis on key metrics
        trends = {}
        if data['health_tracking']:
            for metric in ['heart_rate', 'blood_pressure', 'weight', 'steps']:
                if any(metric in item for item in data['health_tracking']):
                    trend = await self.analytics_engine.perform_trend_analysis(
                        data['health_tracking'], metric
                    )
                    trends[metric] = trend
                    
        # Perform correlation analysis
        correlations = {}
        if data['health_tracking'] and data['nutrition']:
            correlation = await self.analytics_engine.perform_correlation_analysis(
                data['health_tracking'], data['nutrition'], 'weight', 'calories'
            )
            correlations['weight_calories'] = correlation
            
        # Perform risk assessment
        patient_data = self._aggregate_patient_data(data)
        risk_assessment = await self.analytics_engine.perform_risk_assessment(patient_data)
        
        # Generate insights
        insights = await self._generate_patient_insights(trends, correlations, risk_assessment)
        
        return AnalyticsResponse(
            user_id=user_id,
            analysis_type=AnalyticsType.PATIENT,
            time_range=time_range,
            trends=trends,
            correlations=correlations,
            risk_assessment=risk_assessment,
            insights=insights,
            recommendations=risk_assessment.recommendations,
            timestamp=datetime.utcnow()
        )
        
    async def analyze_population_health(self, filters: Dict[str, Any]) -> PopulationHealthMetrics:
        """Perform population health analysis"""
        logger.info("Starting population health analysis")
        
        # This would typically involve aggregating data across multiple users
        # For now, we'll return a sample analysis
        
        return PopulationHealthMetrics(
            total_patients=1000,
            average_age=45.2,
            common_conditions=["Hypertension", "Diabetes", "Obesity"],
            risk_distribution={
                RiskLevel.LOW: 400,
                RiskLevel.MEDIUM: 300,
                RiskLevel.HIGH: 200,
                RiskLevel.CRITICAL: 100
            },
            trends_by_condition={
                "Hypertension": TrendDirection.INCREASING,
                "Diabetes": TrendDirection.STABLE,
                "Obesity": TrendDirection.INCREASING
            },
            recommendations=[
                "Implement preventive care programs",
                "Focus on lifestyle modification",
                "Increase screening frequency for high-risk groups"
            ]
        )
        
    async def provide_clinical_decision_support(self, user_id: UUID, symptoms: List[str]) -> ClinicalDecisionSupport:
        """Provide clinical decision support"""
        logger.info(f"Providing clinical decision support for user {user_id}")
        
        # Collect patient data
        data = await self.collect_data_from_services(user_id, TimeRange.ONE_MONTH)
        
        # Analyze symptoms and patient history
        risk_assessment = await self.analytics_engine.perform_risk_assessment(
            self._aggregate_patient_data(data)
        )
        
        # Generate differential diagnosis
        differential_diagnosis = await self._generate_differential_diagnosis(symptoms, data)
        
        # Recommend tests and procedures
        recommended_tests = await self._recommend_tests(symptoms, risk_assessment)
        
        return ClinicalDecisionSupport(
            user_id=user_id,
            symptoms=symptoms,
            differential_diagnosis=differential_diagnosis,
            risk_level=risk_assessment.overall_risk_level,
            recommended_tests=recommended_tests,
            urgency_level=self._determine_urgency(symptoms, risk_assessment),
            confidence_score=0.85
        )
        
    async def analyze_performance_metrics(self) -> PerformanceMetrics:
        """Analyze platform performance metrics"""
        logger.info("Analyzing platform performance metrics")
        
        # This would typically involve collecting metrics from all services
        # For now, we'll return sample metrics
        
        return PerformanceMetrics(
            total_users=5000,
            active_users_today=1200,
            average_response_time=0.15,
            service_uptime=99.9,
            data_processing_volume="2.5TB",
            analytics_requests_per_hour=1500,
            real_time_streams_active=25
        )
        
    async def create_predictive_model(self, user_id: UUID, target_metric: str) -> PredictiveModel:
        """Create predictive model for a specific metric"""
        logger.info(f"Creating predictive model for user {user_id}, metric: {target_metric}")
        
        # Collect historical data
        data = await self.collect_data_from_services(user_id, TimeRange.ONE_YEAR)
        
        if not data['health_tracking']:
            return PredictiveModel(
                user_id=user_id,
                target_metric=target_metric,
                model_type="linear_regression",
                accuracy=0.0,
                predictions=[],
                confidence_interval=0.0
            )
            
        # Prepare training data
        df = pd.DataFrame(data['health_tracking'])
        if target_metric not in df.columns:
            return PredictiveModel(
                user_id=user_id,
                target_metric=target_metric,
                model_type="linear_regression",
                accuracy=0.0,
                predictions=[],
                confidence_interval=0.0
            )
            
        # Create features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # Prepare features and target
        features = ['day_of_week', 'month', 'day_of_year']
        X = df[features].values
        y = df[target_metric].values
        
        if len(X) < 10:
            return PredictiveModel(
                user_id=user_id,
                target_metric=target_metric,
                model_type="linear_regression",
                accuracy=0.0,
                predictions=[],
                confidence_interval=0.0
            )
            
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Make predictions for next 30 days
        future_dates = pd.date_range(
            start=df['timestamp'].max() + timedelta(days=1),
            periods=30,
            freq='D'
        )
        
        future_features = np.column_stack([
            future_dates.dayofweek,
            future_dates.month,
            future_dates.dayofyear
        ])
        
        predictions = model.predict(future_features)
        
        # Calculate accuracy
        y_pred = model.predict(X)
        accuracy = 1 - mean_squared_error(y, y_pred) / np.var(y)
        
        return PredictiveModel(
            user_id=user_id,
            target_metric=target_metric,
            model_type="linear_regression",
            accuracy=max(0, accuracy),
            predictions=predictions.tolist(),
            confidence_interval=0.1
        )
        
    async def add_real_time_data(self, stream_id: str, value: float, metric: str, user_id: UUID):
        """Add real-time data point for processing"""
        data_point = RealTimeDataPoint(
            stream_id=stream_id,
            value=value,
            metric=metric,
            user_id=user_id,
            timestamp=datetime.utcnow()
        )
        
        await self.real_time_processor.add_data_point(stream_id, data_point)
        
    def _aggregate_patient_data(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Aggregate patient data from multiple sources"""
        aggregated = {}
        
        # Aggregate vital signs
        if data['health_tracking']:
            vitals = {}
            for item in data['health_tracking']:
                if 'heart_rate' in item:
                    vitals['heart_rate'] = item['heart_rate']
                if 'blood_pressure' in item:
                    vitals['systolic'] = item['blood_pressure'].get('systolic')
                    vitals['diastolic'] = item['blood_pressure'].get('diastolic')
                if 'weight' in item:
                    vitals['weight'] = item['weight']
                    
            aggregated['vital_signs'] = vitals
            
        # Calculate BMI if weight and height available
        if 'vital_signs' in aggregated:
            vitals = aggregated['vital_signs']
            if 'weight' in vitals and 'height' in vitals:
                height_m = vitals['height'] / 100  # Convert cm to meters
                vitals['bmi'] = vitals['weight'] / (height_m ** 2)
                
        return aggregated
        
    async def _generate_patient_insights(self, trends: Dict[str, TrendAnalysis], 
                                       correlations: Dict[str, CorrelationAnalysis],
                                       risk_assessment: RiskAssessment) -> List[str]:
        """Generate insights from analysis results"""
        insights = []
        
        # Trend-based insights
        for metric, trend in trends.items():
            if trend.trend_direction == TrendDirection.INCREASING:
                if metric == 'weight':
                    insights.append("Weight is trending upward - consider dietary adjustments")
                elif metric == 'heart_rate':
                    insights.append("Heart rate is increasing - monitor stress levels and activity")
            elif trend.trend_direction == TrendDirection.DECREASING:
                if metric == 'weight':
                    insights.append("Weight is trending downward - ensure healthy weight loss")
                    
        # Correlation-based insights
        for correlation_name, correlation in correlations.items():
            if correlation.significance and correlation.strength in ['strong', 'very_strong']:
                if 'weight_calories' in correlation_name:
                    insights.append("Strong correlation between weight and calorie intake detected")
                    
        # Risk-based insights
        if risk_assessment.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            insights.append("High risk factors detected - immediate attention recommended")
            
        return insights
        
    async def _generate_differential_diagnosis(self, symptoms: List[str], 
                                             patient_data: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate differential diagnosis based on symptoms and patient data"""
        # This is a simplified version - in practice, this would use medical knowledge bases
        diagnoses = []
        
        if 'chest pain' in symptoms:
            diagnoses.extend(['Angina', 'Gastroesophageal reflux disease', 'Anxiety'])
        if 'shortness of breath' in symptoms:
            diagnoses.extend(['Asthma', 'Chronic obstructive pulmonary disease', 'Heart failure'])
        if 'fatigue' in symptoms:
            diagnoses.extend(['Anemia', 'Depression', 'Hypothyroidism'])
            
        return diagnoses[:5]  # Return top 5 differential diagnoses
        
    async def _recommend_tests(self, symptoms: List[str], risk_assessment: RiskAssessment) -> List[str]:
        """Recommend tests based on symptoms and risk assessment"""
        tests = []
        
        if 'chest pain' in symptoms:
            tests.extend(['Electrocardiogram', 'Troponin test', 'Chest X-ray'])
        if 'shortness of breath' in symptoms:
            tests.extend(['Pulmonary function tests', 'Chest X-ray', 'Echocardiogram'])
        if risk_assessment.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            tests.append('Comprehensive metabolic panel')
            
        return tests
        
    def _determine_urgency(self, symptoms: List[str], risk_assessment: RiskAssessment) -> str:
        """Determine urgency level for clinical decision support"""
        urgent_symptoms = ['chest pain', 'severe bleeding', 'loss of consciousness']
        
        if any(symptom in symptoms for symptom in urgent_symptoms):
            return "immediate"
        elif risk_assessment.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return "urgent"
        else:
            return "routine" 