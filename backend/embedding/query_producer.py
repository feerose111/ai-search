from confluent_kafka import Producer
import json
from datetime import datetime
import logging
from uuid import uuid4
from backend.utils.config import KAFKA_BROKER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('query-producer')

class QueryHistoryProducer:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BROKER,
            'client.id': 'query-producer'
        })
        self.topic = 'query_history'

    def delivery_callback(self, err, msg):
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()}')

    def send_query_event(self, raw_query, parsed_query):
        """
        Send query history event to Kafka
        
        Args:
            raw_query: The original user query string
            parsed_query: The parsed query structure
        """
        query_id = str(uuid4())
        
        query_data = {
            "query_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_query": raw_query,
            "parsed_query": parsed_query,
            "intent": parsed_query.get("intent", "unknown"),
            "date_filter": parsed_query.get("date_filter"),
            "amount_filter": parsed_query.get("amount_filter")
        }

        try:
            self.producer.produce(
                topic=self.topic,
                key=query_id,
                value=json.dumps(query_data),
                callback=self.delivery_callback
            )
            self.producer.poll(0)
            logger.info(f"Produced query: {query_id}")
        except Exception as e:
            logger.error(f"Failed to produce query: {str(e)}")
            raise

    def flush(self):
        """Wait for all messages to be delivered"""
        self.producer.flush()
