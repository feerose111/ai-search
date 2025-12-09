from confluent_kafka import Producer
import json
from datetime import datetime
import logging
from uuid import uuid4
from backend_second.utils.config import KAFKA_BROKER

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

    def send_query_event(self, raw_query):

        query_id = str(uuid4())
        
        query_data = {
            "query_id": query_id,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_query": raw_query
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
