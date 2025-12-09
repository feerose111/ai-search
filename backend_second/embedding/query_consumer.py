from confluent_kafka import Consumer
import json
import logging
from datetime import datetime
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
from backend_second.utils.config import KAFKA_BROKER, MILVUS_HOST, MILVUS_PORT, HISTORY_COLLECTION_SECOND,MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('query-consumer')

class QueryHistoryConsumer:
    def __init__(self):
        # Kafka Consumer
        self.consumer = Consumer({
            'bootstrap.servers': KAFKA_BROKER,
            'group.id': 'query-consumers',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        self.topic = 'query_history'

        # Milvus setup
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=10 )
        self.collection = Collection(HISTORY_COLLECTION_SECOND)
        self.embedding_model = SentenceTransformer(MODEL)
        self.collection.load()

    def _generate_embedding(self, text: str):
        """Generate embedding vector for text"""
        return self.embedding_model.encode([text])[0].tolist()

    def process_message(self, message):
        try:
            query_data = json.loads(message.value())

            # Prepare Milvus entity
            entity = {
                "query_id": query_data["query_id"],
                "timestamp": int(datetime.fromisoformat(query_data["timestamp"]).timestamp()),
                "embedding": self._generate_embedding(query_data["raw_query"]),
            }

            # Insert into Milvus
            self.collection.insert([entity])
            logger.info(f"Indexed to Milvus: {query_data['query_id']}")

            self.consumer.commit(message)

        except json.JSONDecodeError:
            logger.error("Failed to decode message")
        except KeyError as e:
            logger.error(f"Missing field: {str(e)}")
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")

    def run(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None: continue
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                self.process_message(msg)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.consumer.close()