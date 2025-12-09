import json
from confluent_kafka import Producer
from backend.utils.config import JSON_URL, COLLECTION_NAME, KAFKA_BROKER
from backend.utils.feature.logger import setup_logger

logger = setup_logger()

BUFFER_COUNT = 0

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
            topic=COLLECTION_NAME,
            value=json.dumps(item).encode('utf-8')
        )
        BUFFER_COUNT += 1
        print(f"✅ Sent to Kafka: {item['id']}")
        logger.info(f"Message sent to Kafka | topic={COLLECTION_NAME} item_id={item['id']} buffer_count={BUFFER_COUNT}")

    producer.flush()
    logger.info(f"Producer flushed successfully | total_messages={BUFFER_COUNT}")

except Exception as e:
    logger.error(f"Error during message production | error={str(e)} messages_sent={BUFFER_COUNT}")
    raise


def get_buffer_count():
    logger.info(f"Buffer count requested | current_count={BUFFER_COUNT}")
    return BUFFER_COUNT
