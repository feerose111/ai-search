import json
from confluent_kafka import Consumer
from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer
from backend_second.utils.config import MILVUS_HOST, MILVUS_PORT, MODEL, COLLECTION_NAME_SECOND, KAFKA_BROKER
from backend_second.utils.db.templates import TEMPLATES
from backend_second.utils.normalizer.normalizer import normalize_document


connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
collection = Collection(COLLECTION_NAME_SECOND)
collection.load()

model = SentenceTransformer(MODEL)

consumer = Consumer({
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'esewa_consumer',
    'auto.offset.reset': 'earliest',
})

consumer.subscribe([COLLECTION_NAME_SECOND])

print("✅ Listening to Kafka...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"⚠️ Kafka error: {msg.error()}")
            continue

        data = json.loads(msg.value().decode('utf-8'))

        doc_type = data.get("type")
        data = normalize_document(data)

        template_func = TEMPLATES.get(doc_type)
        if not template_func:
            print(f"⚠️ Unknown doc_type: {doc_type}")
            continue

        data["text"] = template_func(data)
        print(data['text'])
        embeddings = model.encode(data["text"]).tolist()

        try:
            record = {
                "id": data["id"],
                "user_id": data["user_id"],
                "type": data["type"],
                "category": data["category"],
                "date": data["date"],
                "amount": data["amount"],
                "embedding": embeddings,
                "text": data["text"],
                "metadata": data["metadata"],
            }

            collection.upsert(data=[record])
            print(f"✅ upserted: {data['id']}")
        except Exception as e:
            print(f"⚠️ Failed to insert {data['id']}: {str(e)}\nData: {data}")

except KeyboardInterrupt:
    pass
finally:
    consumer.close()

