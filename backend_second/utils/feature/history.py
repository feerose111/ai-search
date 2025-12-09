import json
from pathlib import Path
from datetime import datetime
import logging ,threading

HISTORY_FILE = Path("backend_second/data/query_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

#===========MIlVUS HISTORY SERVICE===================================

# Global service instance
history_service = None

# Try to initialize Kafka/Milvus history service
from backend_second.embedding.query_producer import QueryHistoryProducer
from backend_second.embedding.query_consumer import QueryHistoryConsumer
try:
    class QueryHistoryService:
        def __init__(self):
            self.producer = QueryHistoryProducer()
            self.consumer = QueryHistoryConsumer()
            self.consumer_thread = None
            logging.info("Kafka-based history service initialized")

        def start_consumer(self):
            """Start consumer in background thread"""
            if not self.consumer_thread:
                self.consumer_thread = threading.Thread(
                    target=self.consumer.run,
                    daemon=True
                )
                self.consumer_thread.start()

        def log_query(self, raw_query: str):
            try:
                self.producer.send_query_event(raw_query)
            except Exception as e:
                logging.error(f"Kafka logging failed: {str(e)}")

        def stop(self):
                """Cleanup resources"""
                if self.producer:
                    self.producer.flush()
                logging.info("History service stopped")

    history_service = QueryHistoryService()
    history_service.start_consumer()

except ImportError:
    logging.warning("Kafka dependencies not available. Using file-based history only.")
except Exception as e:
    logging.error(f"History service initialization failed: {str(e)}")
#===================FILE HISTORY SERVICE=======================

def log_query(raw_query: str, parsed_query: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "raw_query": raw_query,
        "parsed_query": parsed_query
    }
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    history.insert(0, entry)
    history = history[:100]  # Limit to latest 100 queries

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def get_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

