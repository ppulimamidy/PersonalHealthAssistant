"""
Machine Learning Pipeline for Medical Records
Training and management pipeline for AI models used in medical records processing.
"""

import asyncio
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from pathlib import Path

# ML libraries
try:
    import sklearn
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from common.utils.logging import get_logger


class ModelType(str, Enum):
    """Types of ML models."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NER = "ner"
    SUMMARIZATION = "summarization"
    ANOMALY_DETECTION = "anomaly_detection"


class TrainingStatus(str, Enum):
    """Training status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time_seconds: float
    model_size_mb: float
    version: str
    created_at: datetime


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    model_type: ModelType
    model_name: str
    training_data_path: str
    validation_split: float = 0.2
    test_split: float = 0.1
    random_state: int = 42
    max_epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    early_stopping_patience: int = 10
    model_save_path: Optional[str] = None


class MedicalDataset(Dataset):
    """Custom dataset for medical data."""
    
    def __init__(self, texts: List[str], labels: List[str], tokenizer=None):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(labels)
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        
        if self.tokenizer:
            # Tokenize text
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=512,
                return_tensors='pt'
            )
            return {
                'input_ids': encoding['input_ids'].flatten(),
                'attention_mask': encoding['attention_mask'].flatten(),
                'labels': torch.tensor(self.label_encoder.transform([label])[0])
            }
        else:
            # Simple encoding for non-transformer models
            return {
                'text': text,
                'label': self.label_encoder.transform([label])[0]
            }


class DocumentClassifier:
    """Document classification model."""
    
    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.logger = get_logger(__name__)
    
    def train(self, texts: List[str], labels: List[str]) -> ModelMetrics:
        """Train the document classifier."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn not available")
        
        try:
            # Feature extraction
            features = self._extract_features(texts)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Encode labels
            y_train_encoded = self.label_encoder.fit_transform(y_train)
            y_test_encoded = self.label_encoder.transform(y_test)
            
            # Train model
            start_time = datetime.now()
            
            if self.model_type == "random_forest":
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif self.model_type == "gradient_boosting":
                self.model = GradientBoostingClassifier(random_state=42)
            elif self.model_type == "logistic_regression":
                self.model = LogisticRegression(random_state=42)
            elif self.model_type == "svm":
                self.model = SVC(random_state=42)
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            self.model.fit(X_train_scaled, y_train_encoded)
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test_encoded, y_pred)
            
            # Calculate metrics
            metrics = ModelMetrics(
                accuracy=accuracy,
                precision=0.8,  # Placeholder
                recall=0.8,     # Placeholder
                f1_score=0.8,   # Placeholder
                training_time_seconds=training_time,
                model_size_mb=0.1,  # Placeholder
                version="1.0.0",
                created_at=datetime.now()
            )
            
            self.logger.info(f"✅ Document classifier trained successfully. Accuracy: {accuracy:.3f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Document classifier training failed: {e}")
            raise
    
    def predict(self, text: str) -> Dict[str, Any]:
        """Predict document type."""
        if not self.model:
            raise ValueError("Model not trained")
        
        # Extract features
        features = self._extract_features([text])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        # Decode label
        predicted_label = self.label_encoder.inverse_transform([prediction])[0]
        
        return {
            "predicted_type": predicted_label,
            "confidence": float(max(probability)),
            "probabilities": {
                label: float(prob) for label, prob in zip(self.label_encoder.classes_, probability)
            }
        }
    
    def _extract_features(self, texts: List[str]) -> np.ndarray:
        """Extract features from texts."""
        features = []
        
        for text in texts:
            text_features = []
            
            # Basic text features
            text_features.append(len(text))  # Length
            text_features.append(len(text.split()))  # Word count
            text_features.append(len([c for c in text if c.isupper()]))  # Uppercase count
            
            # Medical terminology features
            medical_terms = [
                "diagnosis", "symptom", "treatment", "medication", "procedure",
                "lab", "test", "result", "imaging", "x-ray", "ct", "mri",
                "blood", "urine", "biopsy", "surgery", "prescription"
            ]
            
            for term in medical_terms:
                text_features.append(text.lower().count(term))
            
            # Numerical features
            numbers = re.findall(r'\d+', text)
            text_features.append(len(numbers))
            
            features.append(text_features)
        
        return np.array(features)
    
    def save_model(self, path: str):
        """Save the trained model."""
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "label_encoder": self.label_encoder,
            "model_type": self.model_type
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        self.logger.info(f"✅ Model saved to {path}")
    
    def load_model(self, path: str):
        """Load a trained model."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.label_encoder = model_data["label_encoder"]
        self.model_type = model_data["model_type"]
        
        self.logger.info(f"✅ Model loaded from {path}")


class UrgencyPredictor:
    """Urgency prediction model."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.logger = get_logger(__name__)
    
    def train(self, texts: List[str], urgency_scores: List[float]) -> ModelMetrics:
        """Train the urgency predictor."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn not available")
        
        try:
            # Feature extraction
            features = self._extract_urgency_features(texts)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, urgency_scores, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            start_time = datetime.now()
            
            self.model = GradientBoostingRegressor(random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mse = np.mean((y_test - y_pred) ** 2)
            r2 = self.model.score(X_test_scaled, y_test)
            
            # Calculate metrics
            metrics = ModelMetrics(
                accuracy=r2,
                precision=0.0,  # Not applicable for regression
                recall=0.0,     # Not applicable for regression
                f1_score=0.0,   # Not applicable for regression
                training_time_seconds=training_time,
                model_size_mb=0.1,
                version="1.0.0",
                created_at=datetime.now()
            )
            
            self.logger.info(f"✅ Urgency predictor trained successfully. R²: {r2:.3f}, MSE: {mse:.3f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Urgency predictor training failed: {e}")
            raise
    
    def predict(self, text: str) -> float:
        """Predict urgency score."""
        if not self.model:
            raise ValueError("Model not trained")
        
        # Extract features
        features = self._extract_urgency_features([text])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        urgency_score = self.model.predict(features_scaled)[0]
        return max(0.0, min(1.0, urgency_score))  # Clamp between 0 and 1
    
    def _extract_urgency_features(self, texts: List[str]) -> np.ndarray:
        """Extract urgency-related features."""
        features = []
        
        urgency_keywords = [
            "critical", "urgent", "emergency", "stat", "immediate",
            "abnormal", "elevated", "decreased", "high", "low",
            "cancer", "malignant", "tumor", "metastasis",
            "infection", "sepsis", "bacteremia", "fungemia",
            "bleeding", "hemorrhage", "anemia", "thrombocytopenia",
            "heart attack", "myocardial infarction", "chest pain",
            "stroke", "cva", "tia", "neurological deficit"
        ]
        
        for text in texts:
            text_features = []
            text_lower = text.lower()
            
            # Count urgency keywords
            for keyword in urgency_keywords:
                text_features.append(text_lower.count(keyword))
            
            # Count exclamation marks and caps
            text_features.append(text.count('!'))
            text_features.append(len([c for c in text if c.isupper()]))
            
            # Check for time-sensitive words
            time_words = ["now", "immediately", "asap", "stat", "urgent"]
            text_features.append(sum(text_lower.count(word) for word in time_words))
            
            features.append(text_features)
        
        return np.array(features)


class MLPipeline:
    """Machine learning pipeline for medical records."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.models = {}
        self.training_status = TrainingStatus.PENDING
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models."""
        try:
            self.models = {
                "document_classifier": DocumentClassifier(),
                "urgency_predictor": UrgencyPredictor()
            }
            
            # Load pre-trained models if available
            self._load_pretrained_models()
            
            self.logger.info("✅ ML pipeline initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize ML pipeline: {e}")
    
    def _load_pretrained_models(self):
        """Load pre-trained models from disk."""
        for model_name, model in self.models.items():
            model_path = self.models_dir / f"{model_name}.pkl"
            if model_path.exists():
                try:
                    model.load_model(str(model_path))
                    self.logger.info(f"✅ Loaded pre-trained model: {model_name}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to load {model_name}: {e}")
    
    async def train_models(self, training_data: Dict[str, Any]) -> Dict[str, ModelMetrics]:
        """Train all models with provided data."""
        self.training_status = TrainingStatus.RUNNING
        
        try:
            self.logger.info("🚀 Starting model training")
            
            results = {}
            
            # Train document classifier
            if "document_data" in training_data:
                doc_data = training_data["document_data"]
                results["document_classifier"] = self.models["document_classifier"].train(
                    doc_data["texts"], doc_data["labels"]
                )
                
                # Save model
                model_path = self.models_dir / "document_classifier.pkl"
                self.models["document_classifier"].save_model(str(model_path))
            
            # Train urgency predictor
            if "urgency_data" in training_data:
                urgency_data = training_data["urgency_data"]
                results["urgency_predictor"] = self.models["urgency_predictor"].train(
                    urgency_data["texts"], urgency_data["scores"]
                )
                
                # Save model
                model_path = self.models_dir / "urgency_predictor.pkl"
                self.models["urgency_predictor"].save_model(str(model_path))
            
            self.training_status = TrainingStatus.COMPLETED
            self.logger.info("✅ Model training completed successfully")
            
            return results
            
        except Exception as e:
            self.training_status = TrainingStatus.FAILED
            self.logger.error(f"❌ Model training failed: {e}")
            raise
    
    async def predict_document_type(self, text: str) -> Dict[str, Any]:
        """Predict document type."""
        if "document_classifier" not in self.models:
            raise ValueError("Document classifier not available")
        
        return self.models["document_classifier"].predict(text)
    
    async def predict_urgency(self, text: str) -> float:
        """Predict urgency score."""
        if "urgency_predictor" not in self.models:
            raise ValueError("Urgency predictor not available")
        
        return self.models["urgency_predictor"].predict(text)
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models."""
        status = {}
        
        for model_name, model in self.models.items():
            status[model_name] = {
                "trained": model.model is not None,
                "model_type": getattr(model, 'model_type', 'unknown'),
                "available": True
            }
        
        status["training_status"] = self.training_status.value
        
        return status
    
    async def generate_training_data(self) -> Dict[str, Any]:
        """Generate synthetic training data for demonstration."""
        # Document classification data
        doc_texts = [
            "Complete Blood Count shows normal values",
            "Chest X-ray reveals no abnormalities",
            "Patient presents with chest pain and shortness of breath",
            "Blood glucose level is elevated at 180 mg/dL",
            "MRI scan shows mass in the right lung",
            "Urinalysis results are within normal limits",
            "Patient diagnosed with diabetes mellitus",
            "CT scan reveals pulmonary embolism",
            "Lab results show elevated creatinine levels",
            "EKG shows normal sinus rhythm"
        ]
        
        doc_labels = [
            "lab_report", "imaging_report", "clinical_note", "lab_report",
            "imaging_report", "lab_report", "clinical_note", "imaging_report",
            "lab_report", "imaging_report"
        ]
        
        # Urgency prediction data
        urgency_texts = [
            "Normal lab results, no action required",
            "Slightly elevated blood pressure, monitor",
            "Critical lab values, immediate attention needed",
            "Patient stable, routine follow-up",
            "Emergency situation, stat response required",
            "Abnormal findings, urgent evaluation needed",
            "Routine check-up, no concerns",
            "Severe symptoms, immediate medical attention",
            "Mild symptoms, continue monitoring",
            "Life-threatening condition, emergency care"
        ]
        
        urgency_scores = [0.1, 0.3, 0.9, 0.2, 1.0, 0.8, 0.1, 0.9, 0.4, 1.0]
        
        return {
            "document_data": {
                "texts": doc_texts,
                "labels": doc_labels
            },
            "urgency_data": {
                "texts": urgency_texts,
                "scores": urgency_scores
            }
        }


# Global ML pipeline instance
ml_pipeline = MLPipeline() 