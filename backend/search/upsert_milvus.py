import atexit
import json
from backend.utils.config import COLLECTION_NAME, KAFKA_BROKER
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def send_to_kafka(document):
    try:
        producer.produce(
            topic=COLLECTION_NAME,
            value=json.dumps(document).encode('utf-8')
        )
        return True

    except Exception as e:
        print(f"⚠️ Kafka error: {e}")
        return False

def upsert_ingestion(data):
    if isinstance(data, dict):
        return send_to_kafka(data)

    if isinstance(data, list):
        results = [send_to_kafka(doc) for doc in data]
        return all(results)
    return False

atexit.register(producer.flush, 10)
