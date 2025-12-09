import json
from confluent_kafka import Producer
from backend_second.utils.config import JSON_URL, COLLECTION_NAME_SECOND, KAFKA_BROKER
from backend_second.utils.feature.logger import setup_logger

logger = setup_logger()

try:
    with open(JSON_URL, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    logger.info(f"Dataset loaded successfully ")
except FileNotFoundError:
    logger.error(f"Dataset file not found ")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in dataset file ")
    raise
except Exception as e:
    logger.error(f"Failed to load dataset ")
    raise

try:
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    logger.info(f"Kafka producer initialized ")
except Exception as e:
    logger.error(f"Failed to initialize Kafka producer ")
    raise

try:
    for item in dataset:
        producer.produce(
            topic=COLLECTION_NAME_SECOND,
            value=json.dumps(item).encode('utf-8')
        )
        print(f"✅ Sent to Kafka: {item['id']}")
        logger.info(f"Message sent to Kafka: {item['id']} ")

    producer.flush()
    logger.info(f"Producer flushed successfully")

except Exception as e:
    logger.error(f"Error during message production")
    raise

