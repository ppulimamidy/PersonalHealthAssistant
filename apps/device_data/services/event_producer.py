"""
Event Producer Service
Handles publishing device data events to Kafka for real-time processing.
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.cimpl import KafkaError

from common.config.settings import get_settings
from common.utils.logging import get_logger
from ..models.data_point import DeviceDataPoint
from ..models.device import Device

logger = get_logger(__name__)
settings = get_settings()


class DeviceDataEventProducer:
    """
    Kafka producer for device data events.
    Handles publishing raw data, processed data, anomalies, and calibration events.
    """
    
    def __init__(self):
        self.producer = None
        self.topics = {
            "raw_data": "device-data-raw",
            "processed_data": "device-data-processed", 
            "anomalies": "device-anomalies",
            "calibration_events": "calibration-events",
            "data_quality_issues": "data-quality-issues",
            "sync_events": "sync-events"
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
        """Initialize Kafka producer"""
        try:
            logger.info(f"🔧 Initializing Kafka producer with bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            # Create producer configuration
            producer_config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'client.id': 'device-data-producer',
                'acks': 'all',
                'retries': 3,
                'max.in.flight.requests.per.connection': 1,
                'enable.idempotence': True,
                'compression.type': 'snappy',
                'batch.size': 16384,
                'linger.ms': 10
            }
            
            self.producer = Producer(producer_config)
            logger.info("✅ Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    async def publish_raw_data(self, data_point: DeviceDataPoint) -> bool:
        """
        Publish raw device data to Kafka.
        
        Args:
            data_point: Raw data point from device
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            event = {
                "event_type": "raw_data_received",
                "timestamp": datetime.utcnow().isoformat(),
                "data_point_id": str(data_point.id),
                "device_id": str(data_point.device_id),
                "data_type": data_point.data_type,
                "value": data_point.value,
                "unit": data_point.unit,
                "quality": data_point.quality,
                "metadata": data_point.metadata
            }
            
            logger.debug(f"📤 Publishing raw data event: device_id={data_point.device_id}, data_type={data_point.data_type}, value={data_point.value}")
            
            # Serialize the event
            event_json = json.dumps(event, default=str)
            
            # Use device_id as key for partitioning
            self.producer.produce(
                topic=self.topics["raw_data"],
                key=str(data_point.device_id).encode('utf-8'),
                value=event_json.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Flush to ensure delivery
            self.producer.flush(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["raw_data"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            logger.info(f"✅ Published raw data event (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing raw data: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing raw data: {e}")
            return False
    
    def _delivery_report(self, err, msg):
        """Delivery report callback for Kafka producer"""
        if err is not None:
            logger.error(f"❌ Message delivery failed: {err}")
            self.metrics["failed_events"] += 1
        else:
            logger.debug(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    async def publish_processed_data(self, data_point: DeviceDataPoint) -> bool:
        """
        Publish processed and validated device data to Kafka.
        
        Args:
            data_point: Processed data point
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            event = {
                "event_type": "data_processed",
                "timestamp": datetime.utcnow().isoformat(),
                "data_point_id": str(data_point.id),
                "device_id": str(data_point.device_id),
                "data_type": data_point.data_type,
                "value": data_point.value,
                "unit": data_point.unit,
                "quality": data_point.quality,
                "processing_metadata": {
                    "validated": True,
                    "outliers_removed": False,
                    "normalized": False,
                    "calibration_applied": False
                }
            }
            
            logger.debug(f"📤 Publishing processed data event: device_id={data_point.device_id}, data_type={data_point.data_type}")
            
            future = self.producer.produce(
                self.topics["processed_data"],
                key=str(data_point.device_id),
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["processed_data"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published processed data event: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset} (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing processed data: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing processed data: {e}")
            return False
    
    async def publish_device_anomaly(self, anomaly: Dict[str, Any]) -> bool:
        """
        Publish device anomaly event to Kafka.
        
        Args:
            anomaly: Anomaly data dictionary
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            event = {
                "event_type": "device_anomaly_detected",
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": anomaly.get("device_id"),
                "device_name": anomaly.get("device_name"),
                "anomaly_type": anomaly.get("anomaly_type"),
                "severity": anomaly.get("severity"),
                "description": anomaly.get("description"),
                "anomaly_data": anomaly
            }
            
            logger.warning(f"🚨 Publishing device anomaly: device_id={anomaly.get('device_id')}, type={anomaly.get('anomaly_type')}, severity={anomaly.get('severity')}")
            
            future = self.producer.produce(
                self.topics["anomalies"],
                key=anomaly.get("device_id"),
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["anomalies"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published anomaly event: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset} (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing anomaly: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing anomaly: {e}")
            return False
    
    async def publish_calibration_event(self, event: Dict[str, Any]) -> bool:
        """
        Publish calibration event to Kafka.
        
        Args:
            event: Calibration event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            kafka_event = {
                "event_type": "calibration_event",
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": event.get("device_id"),
                "device_name": event.get("device_name"),
                "calibration_type": event.get("calibration_type"),
                "calibration_data": event
            }
            
            logger.info(f"🔧 Publishing calibration event: device_id={event.get('device_id')}, type={event.get('calibration_type')}")
            
            future = self.producer.produce(
                self.topics["calibration_events"],
                key=event.get("device_id"),
                value=kafka_event
            )
            
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["calibration_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published calibration event: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset} (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing calibration event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing calibration event: {e}")
            return False
    
    async def publish_data_quality_issue(self, issue: Dict[str, Any]) -> bool:
        """
        Publish data quality issue to Kafka.
        
        Args:
            issue: Data quality issue data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            event = {
                "event_type": "data_quality_issue",
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": issue.get("device_id"),
                "device_name": issue.get("device_name"),
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
                "description": issue.get("description"),
                "issue_data": issue
            }
            
            logger.warning(f"⚠️ Publishing data quality issue: device_id={issue.get('device_id')}, type={issue.get('issue_type')}, severity={issue.get('severity')}")
            
            future = self.producer.produce(
                self.topics["data_quality_issues"],
                key=issue.get("device_id"),
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["data_quality_issues"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published data quality issue: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset} (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing data quality issue: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing data quality issue: {e}")
            return False
    
    async def publish_sync_event(self, sync_data: Dict[str, Any]) -> bool:
        """
        Publish sync event to Kafka.
        
        Args:
            sync_data: Sync event data
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        start_time = time.time()
        try:
            event = {
                "event_type": "sync_event",
                "timestamp": datetime.utcnow().isoformat(),
                "device_id": sync_data.get("device_id"),
                "device_name": sync_data.get("device_name"),
                "sync_type": sync_data.get("sync_type"),
                "sync_status": sync_data.get("sync_status"),
                "sync_data": sync_data
            }
            
            logger.info(f"🔄 Publishing sync event: device_id={sync_data.get('device_id')}, type={sync_data.get('sync_type')}, status={sync_data.get('sync_status')}")
            
            future = self.producer.produce(
                self.topics["sync_events"],
                key=sync_data.get("device_id"),
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            # Update metrics
            self.metrics["total_events_published"] += 1
            self.metrics["events_by_topic"][self.topics["sync_events"]] += 1
            self.metrics["last_publish_time"] = datetime.utcnow()
            
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published sync event: {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset} (took {publish_time:.2f}ms)")
            return True
            
        except KafkaError as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Kafka error publishing sync event: {e}")
            return False
        except Exception as e:
            self.metrics["failed_events"] += 1
            logger.error(f"❌ Error publishing sync event: {e}")
            return False
    
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
        
        start_time = time.time()
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
                event_json = json.dumps(event, default=str)
                self.producer.produce(
                    topic,
                    key=str(event.get("device_id")).encode("utf-8") if event.get("device_id") else None,
                    value=event_json.encode("utf-8"),
                    callback=delivery_callback
                )
            self.producer.flush(timeout=10)
            # Update metrics
            self.metrics["total_events_published"] += len(events)
            if topic in self.metrics["events_by_topic"]:
                self.metrics["events_by_topic"][topic] += len(events)
            self.metrics["last_publish_time"] = datetime.utcnow()
            publish_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Published {len(events)} events to topic {topic} (took {publish_time:.2f}ms)")
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
        """Get producer metrics"""
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
        """Close the Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("✅ Kafka producer closed")


# Global producer instance
_event_producer = None


async def get_event_producer() -> DeviceDataEventProducer:
    """Get the global event producer instance"""
    global _event_producer
    if _event_producer is None:
        _event_producer = DeviceDataEventProducer()
    return _event_producer


async def close_event_producer():
    """Close the global event producer"""
    global _event_producer
    if _event_producer:
        _event_producer.close()
        _event_producer = None 