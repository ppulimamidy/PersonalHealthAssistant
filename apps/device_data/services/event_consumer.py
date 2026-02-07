"""
Event Consumer Service
Handles consuming device data events from Kafka for real-time processing.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.cimpl import Message

from common.config.settings import get_settings
from common.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DeviceDataEventConsumer:
    """
    Kafka consumer for device data events.
    Handles consuming raw data, processed data, anomalies, and calibration events.
    """
    
    def __init__(self):
        self.consumers = {}
        self.running = False
        self.topics = {
            "raw_data": "device-data-raw",
            "processed_data": "device-data-processed", 
            "anomalies": "device-anomalies",
            "calibration_events": "calibration-events",
            "data_quality_issues": "data-quality-issues",
            "sync_events": "sync-events"
        }
        self.message_handlers = {}
        self._initialize_consumers()
    
    def _initialize_consumers(self):
        """Initialize Kafka consumers for each topic"""
        try:
            for topic_name, topic in self.topics.items():
                consumer_config = {
                    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                    'group.id': f'device-data-consumer-{topic_name}',
                    'auto.offset.reset': 'latest',
                    'enable.auto.commit': True,
                    'auto.commit.interval.ms': 1000,
                    'session.timeout.ms': 30000,
                    'heartbeat.interval.ms': 3000,
                    'max.poll.interval.ms': 300000,
                    'fetch.min.bytes': 1,
                    'fetch.max.wait.ms': 1000
                }
                
                consumer = Consumer(consumer_config)
                consumer.subscribe([topic])
                self.consumers[topic_name] = consumer
                logger.info(f"✅ Kafka consumer initialized for topic: {topic}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka consumers: {e}")
    
    def register_handler(self, topic: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a message handler for a specific topic.
        
        Args:
            topic: Topic name
            handler: Function to handle messages from this topic
        """
        self.message_handlers[topic] = handler
        logger.info(f"✅ Registered handler for topic: {topic}")
    
    async def start_consuming(self):
        """Start consuming messages from all topics"""
        if self.running:
            logger.warning("Consumer is already running")
            return
        
        self.running = True
        logger.info("🚀 Starting Kafka consumers...")
        
        # Start consumer tasks for each topic
        tasks = []
        for topic_name, consumer in self.consumers.items():
            task = asyncio.create_task(self._consume_topic(topic_name, consumer))
            tasks.append(task)
        
        try:
            # Wait for all consumer tasks
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Error in consumer tasks: {e}")
        finally:
            self.running = False
    
    async def _consume_topic(self, topic_name: str, consumer: Consumer):
        """Consume messages from a specific topic"""
        logger.info(f"📡 Starting consumer for topic: {topic_name}")
        
        try:
            while self.running:
                try:
                    # Poll for messages with timeout
                    msg = consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.debug(f"Reached end of partition for {topic_name}")
                        else:
                            logger.error(f"❌ Consumer error: {msg.error()}")
                        continue
                    
                    # Parse message
                    try:
                        event_data = json.loads(msg.value().decode('utf-8'))
                        event_type = event_data.get("event_type")
                        timestamp = event_data.get("timestamp")
                        
                        logger.debug(f"📨 Received {event_type} event from {topic_name} at {timestamp}")
                        
                        # Handle message
                        await self._handle_message(topic_name, event_data)
                        
                        # Commit offset
                        consumer.commit(msg)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to parse message from {topic_name}: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error processing message from {topic_name}: {e}")
                        # Continue processing other messages
                        
                except KafkaException as e:
                    logger.error(f"❌ Kafka error in {topic_name}: {e}")
                    if not self.running:
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error consuming from topic {topic_name}: {e}")
        finally:
            consumer.close()
            logger.info(f"🛑 Stopped consumer for topic: {topic_name}")
    
    async def _handle_message(self, topic: str, event_data: Dict[str, Any]):
        """Handle a message from a specific topic"""
        try:
            # Get registered handler for this topic
            handler = self.message_handlers.get(topic)
            if handler:
                # Call handler function
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            else:
                # Default handling based on event type
                await self._default_message_handler(topic, event_data)
                
        except Exception as e:
            logger.error(f"❌ Error in message handler for topic {topic}: {e}")
    
    async def _default_message_handler(self, topic: str, event_data: Dict[str, Any]):
        """Default message handler for unhandled topics"""
        event_type = event_data.get("event_type")
        device_id = event_data.get("device_id")
        
        logger.info(f"📋 Default handling for {event_type} event from device {device_id}")
        
        # Route to appropriate handler based on event type
        if event_type == "raw_data_received":
            await self._handle_raw_data(event_data)
        elif event_type == "data_processed":
            await self._handle_processed_data(event_data)
        elif event_type == "device_anomaly_detected":
            await self._handle_anomaly(event_data)
        elif event_type == "calibration_event":
            await self._handle_calibration_event(event_data)
        elif event_type == "data_quality_issue":
            await self._handle_data_quality_issue(event_data)
        elif event_type == "sync_event":
            await self._handle_sync_event(event_data)
        else:
            logger.warning(f"⚠️ Unknown event type: {event_type}")
    
    async def _handle_raw_data(self, event_data: Dict[str, Any]):
        """Handle raw data events"""
        device_id = event_data.get("device_id")
        data_type = event_data.get("data_type")
        value = event_data.get("value")
        
        logger.info(f"📊 Processing raw data: {data_type} = {value} from device {device_id}")
        
        # Here you would typically:
        # 1. Validate the data
        # 2. Store in database
        # 3. Trigger data quality analysis
        # 4. Forward to health tracking service
        
        # For now, just log the event
        logger.debug(f"Raw data event processed: {event_data}")
    
    async def _handle_processed_data(self, event_data: Dict[str, Any]):
        """Handle processed data events"""
        device_id = event_data.get("device_id")
        data_type = event_data.get("data_type")
        value = event_data.get("value")
        
        logger.info(f"✅ Processing validated data: {data_type} = {value} from device {device_id}")
        
        # Here you would typically:
        # 1. Store processed data
        # 2. Trigger health analysis
        # 3. Update device metrics
        # 4. Send to analytics pipeline
        
        logger.debug(f"Processed data event handled: {event_data}")
    
    async def _handle_anomaly(self, event_data: Dict[str, Any]):
        """Handle device anomaly events"""
        device_id = event_data.get("device_id")
        anomaly_type = event_data.get("anomaly_type")
        severity = event_data.get("severity")
        
        logger.warning(f"🚨 Device anomaly detected: {anomaly_type} (severity: {severity}) for device {device_id}")
        
        # Here you would typically:
        # 1. Create alert/notification
        # 2. Update device status
        # 3. Trigger diagnostic analysis
        # 4. Send to monitoring system
        
        logger.debug(f"Anomaly event handled: {event_data}")
    
    async def _handle_calibration_event(self, event_data: Dict[str, Any]):
        """Handle calibration events"""
        device_id = event_data.get("device_id")
        calibration_type = event_data.get("calibration_type")
        
        logger.info(f"🔧 Calibration event: {calibration_type} for device {device_id}")
        
        # Here you would typically:
        # 1. Update device calibration status
        # 2. Apply calibration corrections
        # 3. Schedule next calibration
        # 4. Update accuracy metrics
        
        logger.debug(f"Calibration event handled: {event_data}")
    
    async def _handle_data_quality_issue(self, event_data: Dict[str, Any]):
        """Handle data quality issues"""
        device_id = event_data.get("device_id")
        issue_type = event_data.get("issue_type")
        severity = event_data.get("severity")
        
        logger.warning(f"⚠️ Data quality issue: {issue_type} (severity: {severity}) for device {device_id}")
        
        # Here you would typically:
        # 1. Flag data for review
        # 2. Trigger data cleaning
        # 3. Update quality metrics
        # 4. Notify data team
        
        logger.debug(f"Data quality issue handled: {event_data}")
    
    async def _handle_sync_event(self, event_data: Dict[str, Any]):
        """Handle sync events"""
        device_id = event_data.get("device_id")
        sync_type = event_data.get("sync_type")
        sync_status = event_data.get("sync_status")
        
        logger.info(f"🔄 Sync event: {sync_type} - {sync_status} for device {device_id}")
        
        # Here you would typically:
        # 1. Update device sync status
        # 2. Update last sync timestamp
        # 3. Trigger data processing
        # 4. Update sync metrics
        
        logger.debug(f"Sync event handled: {event_data}")
    
    async def consume_single_message(self, topic: str, timeout_ms: int = 5000) -> Optional[Dict[str, Any]]:
        """
        Consume a single message from a specific topic.
        
        Args:
            topic: Topic to consume from
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Message data or None if no message available
        """
        try:
            consumer = self.consumers.get(topic)
            if not consumer:
                logger.error(f"❌ No consumer found for topic: {topic}")
                return None
            
            # Poll for a single message
            msg = consumer.poll(timeout=timeout_ms / 1000.0)
            
            if msg is None:
                return None
            
            if msg.error():
                logger.error(f"❌ Consumer error: {msg.error()}")
                return None
            
            # Parse and return message
            event_data = json.loads(msg.value().decode('utf-8'))
            consumer.commit(msg)
            
            return event_data
            
        except Exception as e:
            logger.error(f"❌ Error consuming single message from {topic}: {e}")
            return None
    
    async def consume_batch(self, topic: str, max_messages: int = 10, timeout_ms: int = 5000) -> List[Dict[str, Any]]:
        """
        Consume multiple messages from a specific topic.
        
        Args:
            topic: Topic to consume from
            max_messages: Maximum number of messages to consume
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of message data
        """
        try:
            consumer = self.consumers.get(topic)
            if not consumer:
                logger.error(f"❌ No consumer found for topic: {topic}")
                return []
            
            messages = []
            start_time = datetime.utcnow()
            timeout_seconds = timeout_ms / 1000.0
            
            while len(messages) < max_messages:
                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout_seconds:
                    break
                
                # Poll for message
                remaining_timeout = timeout_seconds - elapsed
                msg = consumer.poll(timeout=remaining_timeout)
                
                if msg is None:
                    break
                
                if msg.error():
                    logger.error(f"❌ Consumer error: {msg.error()}")
                    continue
                
                # Parse message
                try:
                    event_data = json.loads(msg.value().decode('utf-8'))
                    messages.append(event_data)
                    consumer.commit(msg)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse message: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error consuming batch from {topic}: {e}")
            return []
    
    def stop(self):
        """Stop all consumers"""
        logger.info("🛑 Stopping all Kafka consumers...")
        self.running = False
        
        for topic_name, consumer in self.consumers.items():
            try:
                consumer.close()
                logger.info(f"✅ Consumer for {topic_name} stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping consumer for {topic_name}: {e}")
    
    def get_consumer_status(self) -> Dict[str, Any]:
        """Get status of all consumers"""
        status = {
            "running": self.running,
            "consumers": {},
            "total_consumers": len(self.consumers),
            "active_handlers": len(self.message_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for topic_name, consumer in self.consumers.items():
            try:
                # Get consumer statistics
                stats = consumer.get_stats()
                status["consumers"][topic_name] = {
                    "topic": self.topics[topic_name],
                    "has_handler": topic_name in self.message_handlers,
                    "stats": stats
                }
            except Exception as e:
                status["consumers"][topic_name] = {
                    "topic": self.topics[topic_name],
                    "has_handler": topic_name in self.message_handlers,
                    "error": str(e)
                }
        
        return status


# Global instance
_event_consumer = None


async def get_event_consumer() -> DeviceDataEventConsumer:
    """Get the global event consumer instance"""
    global _event_consumer
    if _event_consumer is None:
        _event_consumer = DeviceDataEventConsumer()
    return _event_consumer


async def start_event_consumer():
    """Start the global event consumer"""
    consumer = await get_event_consumer()
    await consumer.start_consuming()


async def stop_event_consumer():
    """Stop the global event consumer"""
    global _event_consumer
    if _event_consumer:
        _event_consumer.stop()
        _event_consumer = None 