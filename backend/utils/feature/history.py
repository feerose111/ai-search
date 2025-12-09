import redis
import json
import uuid
import logging
from datetime import datetime

# === Redis Setup ===
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
REDIS_KEY = "query_history"

# === Redis-based history logging ===
def log_query(raw_query: str, parsed_query: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "raw_query": raw_query,
        "parsed_query": parsed_query
    }
    try:
        r.lpush(REDIS_KEY, json.dumps(entry))   # Add to start
        r.ltrim(REDIS_KEY, 0, 99)               # Keep only latest 100
    except Exception as e:
        logging.warning(f"⚠️ Redis log_query failed: {e}")

def get_history():
    try:
        logs = r.lrange(REDIS_KEY, 0, 99)       # Get latest 100 entries
        return [json.loads(entry) for entry in logs]
    except Exception as e:
        logging.warning(f"⚠️ Redis get_history failed: {e}")
        return []

# === Elasticsearch structured logging ===
def log_query_to_history(es_client, raw_query: str, parsed_query: dict):
    try:
        doc = {
            "query_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow(),
            "raw_query": raw_query,
            "intent": parsed_query.get("intent", "unknown"),
            "parsed_query": parsed_query,
            "date_filter": parsed_query.get("date_filter", {})
        }

        es_client.index(index="query_history", document=doc)
    except Exception as e:
        logging.warning(f"⚠️ Failed to log query history to Elasticsearch: {e}")
