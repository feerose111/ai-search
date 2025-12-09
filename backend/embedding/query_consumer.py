from confluent_kafka import Consumer
from elasticsearch import Elasticsearch
import json
import logging
from backend.utils.config import KAFKA_BROKER, ES_HOST
from backend.utils.elastic_search.es_client import QUERY_HISTORY_INDEX_NAME


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('query-consumer')

class QueryHistoryConsumer:
    def __init__(self):
        # Initialize Kafka Consumer
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BROKER,
            'group.id': 'query-consumers',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        self.topic = 'query_history'
        
        # Initialize Elasticsearch
        self.es = Elasticsearch(ES_HOST)
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create Elasticsearch index with optimized mapping for query history"""
        if not self.es.indices.exists(index=QUERY_HISTORY_INDEX_NAME):
            mapping = {
                "mappings": {
                    "properties": {
                        "query_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "raw_query": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "keyword": {"type": "keyword", "ignore_above": 256}
                            }
                        },
                        "intent": {"type": "keyword"},
                        "parsed_query": {
                            "properties": {
                                "raw_query": {"type": "text"},
                                "intent": {"type": "keyword"},
                                "amount": {"type": "float"},
                                "amount_filter": {
                                    "properties": {
                                        "operator": {"type": "keyword"},
                                        "value": {"type": "float"}
                                    }
                                },
                                "date": {"type": "date"},
                                "date_filter": {
                                    "properties": {
                                        "operator": {"type": "keyword"},
                                        "start": {"type": "date"},
                                        "end": {"type": "date"}
                                    }
                                }
                            }
                        },
                        "date_filter": {
                            "properties": {
                                "operator": {"type": "keyword"},
                                "start": {"type": "date"},
                                "end": {"type": "date"}
                            }
                        }
                    }
                },
                "settings": {
                    "analysis": {
                        "normalizer": {
                            "lowercase_normalizer": {
                                "type": "custom",
                                "filter": ["lowercase"]
                            }
                        }
                    }
                }
            }
            self.es.indices.create(
                index=QUERY_HISTORY_INDEX_NAME,
                body=mapping
            )
            logger.info(f"Created Elasticsearch index: {QUERY_HISTORY_INDEX_NAME}")

    def _transform_query_data(self, query_data):
        """Transform query data for optimal Elasticsearch indexing"""
        transformed = {
            "query_id": query_data["query_id"],
            "timestamp": query_data["timestamp"],
            "raw_query": query_data["raw_query"],
            "intent": query_data["intent"],
            "parsed_query": query_data["parsed_query"]
        }
        
        # Extract date filter for easier aggregation
        if "date_filter" in query_data["parsed_query"]:
            transformed["date_filter"] = query_data["parsed_query"]["date_filter"]
        
        return transformed

    def process_message(self, message):
        """Process a single query message"""
        try:
            query_data = json.loads(message.value())
            transformed_data = self._transform_query_data(query_data)
            
            # Index to Elasticsearch
            self.es.index(
                index=QUERY_HISTORY_INDEX_NAME,
                id=query_data['query_id'],
                body=transformed_data
            )
            logger.info(f"Indexed query: {query_data['query_id']}")
            
            # Manually commit offset
            self.consumer.commit(message)
            
        except json.JSONDecodeError:
            logger.error("Failed to decode message")
        except KeyError as e:
            logger.error(f"Missing required field: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    def run(self):
        """Start consuming messages"""
        self.consumer.subscribe([self.topic])
        logger.info("Started query history consumer")
        
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                self.process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("Shutting down consumer...")
        finally:
            self.consumer.close()
            logger.info("Consumer stopped")

if __name__ == "__main__":
    consumer = QueryHistoryConsumer()
    consumer.run()