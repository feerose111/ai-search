import json
from confluent_kafka import Consumer
from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer
from datetime import datetime
from backend.utils.config import MILVUS_HOST, MILVUS_PORT, MODEL, COLLECTION_NAME, KAFKA_BROKER
from backend.utils.db.templates import TEMPLATES
from backend.utils.normalizer.normalizer import normalize_document
from backend.utils.elastic_search.es_client import get_es, INDEX_NAME
from backend.utils.feature.logger import setup_logger

logger = setup_logger()

# Connect to services
connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
collection = Collection(COLLECTION_NAME)
collection.load()
model = SentenceTransformer(MODEL)
es = get_es()

consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'esewa_consumer',
    'auto.offset.reset': 'earliest',
})

consumer.subscribe([COLLECTION_NAME])
print("✅ Listening to Kafka...")
logger.info("Started Kafka consumer and listening for messages")


def create_es_document(data):
    """Create Elasticsearch document strictly following our mapping"""
    doc_type = data.get("type")
    if doc_type not in ["transaction", "saved_payment", "service", "product"]:
        logger.error(f"Unknown document type: {doc_type}")
        raise ValueError(f"Unknown document type: {doc_type}")

    base_doc = {
        "id": data["id"],
        "type": doc_type,
        "user_id": data.get("user_id"),
        "category": data.get("category"),
    }

    # Add common description field if present
    if "description" in data:
        base_doc["description"] = data["description"]

    # Type-specific field handling
    if doc_type == "transaction":
        transaction_doc = {
            **base_doc,
            "amount": float(data.get("amount", 0)),
            "currency": data.get("currency", "NPR"),
            "date": data.get("date"),
            "merchant_name": data.get("merchant_name"),
            "status": data.get("status", "pending"),
            "properties": {
                "service_name": data.get("service_name", ""),
                "ip": data.get("ip", "0.0.0.0")
            }
        }
        return {k: v for k, v in transaction_doc.items() if v is not None}

    elif doc_type == "saved_payment":
        return {
            **base_doc,
            "template_name": data.get("template_name", ""),
            "payee_name": data.get("payee_name", ""),
            "amount": float(data.get("amount", 0)),
            "created_at": data.get("created_at", datetime.utcnow().isoformat())
        }

    elif doc_type == "service":
        return {
            **base_doc,
            "title": data.get("title", ""),
            "content": data.get("content", ""),
            "language": data.get("language", "en"),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
        }

    elif doc_type == "product":
        return {
            **base_doc,
            "product_name": data.get("product_name", ""),
            "price": float(data.get("price", 0)),
            "available": bool(data.get("available", False)),
            "vendor": data.get("vendor", ""),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
        }


def process_for_milvus(data):
    """Process data for Milvus vector database"""
    template_func = TEMPLATES.get(data.get("type"))
    if not template_func:
        logger.error(f"No template for type: {data.get('type')}")
        raise ValueError(f"No template for type: {data.get('type')}")

    data["text"] = template_func(data)
    embedding = model.encode(data["text"]).tolist()

    return {
        "id": data["id"],
        "user_id": data.get("user_id"),
        "type": data.get("type"),
        "category": data.get("category"),
        "date": data.get("date"),
        "amount": float(data.get("amount", 0)),
        "embedding": embedding,
        "text": data["text"],
        "metadata": data.get("metadata", {}),
    }

def create_es_document(data):
    """Create Elasticsearch document strictly following our mapping"""
    doc_type = data.get("type")
    if doc_type not in ["transaction", "saved_payment", "service", "product"]:
        raise ValueError(f"Unknown document type: {doc_type}")

    base_doc = {
        "id": data["id"],
        "type": doc_type,
        "user_id": data.get("user_id"),
        "category": data.get("category"),
    }

    # Add common description field if present
    if "description" in data:
        base_doc["description"] = data["description"]

    # Type-specific field handling
    if doc_type == "transaction":
        transaction_doc = {
            **base_doc,
            "amount": float(data.get("amount", 0)),
            "currency": data.get("currency", "NPR"),
            "date": data.get("date"),
            "merchant_name": data.get("merchant_name"),
            "status": data.get("status", "pending"),
            "properties": {
                "service_name": data.get("service_name", ""),
                "ip": data.get("ip", "0.0.0.0")
            }
        }
        return {k: v for k, v in transaction_doc.items() if v is not None}

    elif doc_type == "saved_payment":
        return {
            **base_doc,
            "template_name": data.get("template_name", ""),
            "payee_name": data.get("payee_name", ""),
            "amount": float(data.get("amount", 0)),
            "created_at": data.get("created_at", datetime.utcnow().isoformat())
        }

    elif doc_type == "service":
        return {
            **base_doc,
            "title": data.get("title", ""),
            "content": data.get("content", ""),
            "language": data.get("language", "en"),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
        }

    elif doc_type == "product":
        return {
            **base_doc,
            "product_name": data.get("product_name", ""),
            "price": float(data.get("price", 0)),
            "available": bool(data.get("available", False)),
            "vendor": data.get("vendor", ""),
            "updated_at": data.get("updated_at", datetime.utcnow().isoformat())
        }

def process_for_milvus(data):
    """Process data for Milvus vector database"""
    template_func = TEMPLATES.get(data.get("type"))
    if not template_func:
        raise ValueError(f"No template for type: {data.get('type')}")
    
    data["text"] = template_func(data)
    embedding = model.encode(data["text"]).tolist()
    
    return {
        "id": data["id"],
        "user_id": data.get("user_id"),
        "type": data.get("type"),
        "category": data.get("category"),
        "date": data.get("date"),
        "amount": float(data.get("amount", 0)),
        "embedding": embedding,
        "text": data["text"],
        "metadata": data.get("metadata", {}),
    }

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"⚠️ Kafka error: {msg.error()}")
            logger.error(f"Kafka error: {msg.error()}")
            continue

        try:
            # Parse and normalize data
            data = json.loads(msg.value().decode('utf-8'))
            data = normalize_document(data)
            doc_type = data.get("type")

            # Milvus processing
            try:
                milvus_record = process_for_milvus(data)
                collection.upsert(data=[milvus_record])
                print(f"✅ Upserted to Milvus: {data['id']}")
                logger.info(f"Upserted to Milvus: {data['id']}")
            except Exception as e:
                print(f"⚠️ Failed to insert to Milvus {data['id']}: {str(e)}")
                logger.error(f"Failed to insert to Milvus {data['id']}: {str(e)}")
                continue

            # Elasticsearch processing
            try:
                es_doc = create_es_document(data)
                es.index(index=INDEX_NAME, id=data["id"], document=es_doc)
                print(f"📥 Indexed in Elasticsearch: {data['id']}")
                print(f"Document type: {doc_type}")
                logger.info(f"Indexed in Elasticsearch: {data['id']}, Document type: {doc_type}")
            except Exception as e:
                print(f"⚠️ Failed to index in Elasticsearch: {e}")
                print(f"Problem document: {json.dumps(es_doc, indent=2)}")
                logger.error(f"Failed to index in Elasticsearch: {e}")

        except Exception as e:
            print(f"⚠️ Failed to process message: {e}")
            logger.error(f"Failed to process message: {e}")
            continue

except KeyboardInterrupt:
    logger.info("Consumer interrupted by user")
    pass
finally:
    consumer.close()
    connections.disconnect(alias="default")
    logger.info("Consumer closed and connections disconnected")
