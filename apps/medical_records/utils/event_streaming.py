"""
Event Streaming Utilities for Medical Records
Handles Kafka event publishing for medical records processing.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from confluent_kafka import Producer
from confluent_kafka.cimpl import KafkaError

from common.config.settings import get_settings
from common.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MedicalRecordsEventProducer:
    """Kafka producer for medical records events."""
    
    def __init__(self):
        self.producer = None
        self.topics = {
            "document_events": "medical-records-documents",
            "nlp_events": "medical-records-nlp",
            "lab_events": "medical-records-lab-results",
            "imaging_events": "medical-records-imaging",
            "clinical_events": "medical-records-clinical-reports",
            "ehr_events": "medical-records-ehr-integration",
            "lab_analysis_events": "medical-records-lab-analysis",
            "imaging_analysis_events": "medical-records-imaging-analysis",
            "critical_alert_events": "medical-records-critical-alerts"
        }
        
        # Metrics tracking
        self.metrics = {
            "total_events_published": 0,
            "events_by_topic": {topic: 0 for topic in self.topics.values()},
            "failed_events": 0,
            "last_publish_time": None,
            "startup_time": datetime.utcnow()
        }
        
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer."""
        try:
            logger.info(f"🔧 Initializing Kafka producer for medical records with bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            # Create producer configuration
            producer_config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'client.id': 'medical-records-producer',
                'acks': 'all',
                'retries': 3,
                'max.in.flight.requests.per.connection': 1,
                'enable.idempotence': True,
                'compression.type': 'snappy',
                'batch.size': 16384,
                'linger.ms': 10
            }
            
            self.producer = Producer(producer_config)
            logger.info("✅ Medical Records Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize medical records Kafka producer: {e}")
            self.producer = None
    
    async def publish_document_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish document processing event to Kafka.
        
        Args:
            event: Document event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use document_id as key for partitioning
            document_id = event.get("document_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["document_events"],
                key=document_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["document_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published document event: {event.get('event_type', 'unknown')} for document {document_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing document event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing document event: {e}")
            return False
    
    async def publish_nlp_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish NLP processing event to Kafka.
        
        Args:
            event: NLP event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use document_id as key for partitioning
            document_id = event.get("document_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["nlp_events"],
                key=document_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["nlp_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published NLP event: {event.get('event_type', 'unknown')} for document {document_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing NLP event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing NLP event: {e}")
            return False
    
    async def publish_lab_result_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish lab result event to Kafka.
        
        Args:
            event: Lab result event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["lab_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["lab_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published lab result event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing lab result event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing lab result event: {e}")
            return False
    
    async def publish_imaging_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish imaging event to Kafka.
        
        Args:
            event: Imaging event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["imaging_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["imaging_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published imaging event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing imaging event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing imaging event: {e}")
            return False
    
    async def publish_clinical_report_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish clinical report event to Kafka.
        
        Args:
            event: Clinical report event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["clinical_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["clinical_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published clinical report event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing clinical report event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing clinical report event: {e}")
            return False
    
    async def publish_ehr_integration_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish EHR integration event to Kafka.
        
        Args:
            event: EHR integration event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use system_name as key for partitioning
            system_name = event.get("system_name", "unknown")
            
            self.producer.produce(
                topic=self.topics["ehr_events"],
                key=system_name.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["ehr_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published EHR integration event: {event.get('event_type', 'unknown')} for system {system_name}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing EHR integration event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing EHR integration event: {e}")
            return False
    
    async def publish_lab_analysis_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish lab analysis event to Kafka.
        
        Args:
            event: Lab analysis event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["lab_analysis_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["lab_analysis_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published lab analysis event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing lab analysis event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing lab analysis event: {e}")
            return False
    
    async def publish_imaging_analysis_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish imaging analysis event to Kafka.
        
        Args:
            event: Imaging analysis event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["imaging_analysis_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["imaging_analysis_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published imaging analysis event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing imaging analysis event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing imaging analysis event: {e}")
            return False
    
    async def publish_critical_alert_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish critical alert event to Kafka.
        
        Args:
            event: Critical alert event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use patient_id as key for partitioning
            patient_id = event.get("patient_id", "unknown")
            
            self.producer.produce(
                topic=self.topics["critical_alert_events"],
                key=patient_id.encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["critical_alert_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"🚨 Published critical alert event: {event.get('event_type', 'unknown')} for patient {patient_id}")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing critical alert event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing critical alert event: {e}")
            return False
    
    def _delivery_report(self, err, msg):
        """Delivery report callback for Kafka producer."""
        if err is not None:
            logger.error(f"❌ Message delivery failed: {err}")
            self.metrics["failed_events"] += 1
        else:
            logger.debug(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    async def publish_batch_events(self, events: List[Dict[str, Any]], topic: str) -> bool:
        """
        Publish a batch of events to a specific topic.
        
        Args:
            events: List of event dictionaries
            topic: Kafka topic name
            
        Returns:
            bool: True if all events published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        delivery_results = {"success": 0, "fail": 0}
        
        def delivery_callback(err, msg):
            if err is not None:
                logger.error(f"❌ Message delivery failed: {err}")
                delivery_results["fail"] += 1
            else:
                logger.debug(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                delivery_results["success"] += 1
        
        try:
            logger.info(f"📦 Publishing batch of {len(events)} events to topic: {topic}")
            
            for event in events:
                # Add timestamp if not present
                if "timestamp" not in event:
                    event["timestamp"] = datetime.utcnow().isoformat()
                
                event_json = json.dumps(event, default=str)
                
                # Determine key based on event type
                key = None
                if "document_id" in event:
                    key = event["document_id"]
                elif "patient_id" in event:
                    key = event["patient_id"]
                elif "system_name" in event:
                    key = event["system_name"]
                
                self.producer.produce(
                    topic,
                    key=key.encode("utf-8") if key else None,
                    value=event_json.encode("utf-8"),
                    callback=delivery_callback
                )
            
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += len(events)
            if topic in self.metrics["events_by_topic"]:
                self.metrics["events_by_topic"][topic] += len(events)
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            logger.info(f"✅ Published {len(events)} events to topic {topic}")
            
            # Success if all events delivered
            return delivery_results["fail"] == 0
            
        except KafkaError as e:
            self.metrics["failed_events"] += len(events)
            logger.error(f"❌ Kafka error publishing batch events: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += len(events)
            logger.error(f"❌ Error publishing batch events: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get producer metrics."""
        uptime = (datetime.utcnow() - self.metrics["startup_time"]).total_seconds()
        success_rate = 0
        if self.metrics["total_events_published"] + self.metrics["failed_events"] > 0:
            success_rate = self.metrics["total_events_published"] / (self.metrics["total_events_published"] + self.metrics["failed_events"]) * 100
        
        return {
            "producer_status": "connected" if self.producer else "disconnected",
            "uptime_seconds": uptime,
            "total_events_published": self.metrics["total_events_published"],
            "failed_events": self.metrics["failed_events"],
            "success_rate_percent": round(success_rate, 2),
            "events_by_topic": self.metrics["events_by_topic"],
            "last_publish_time": self.metrics["last_publish_time"].isoformat() if self.metrics["last_publish_time"] else None,
            "startup_time": self.metrics["startup_time"].isoformat()
        }
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.close()
            logger.info("✅ Medical Records Kafka producer closed") 