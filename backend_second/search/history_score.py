import numpy as np
from backend_second.utils.config import HISTORY_COLLECTION_SECOND
from pymilvus import Collection
import time

class HistoryScore:
    def __init__(self):
        self.recent_items = []
        self.last_refresh = 0

    def get_recent_history(self, limit=5):
        """Get recent history items with time-based caching"""
        current_time = time.time()
        if current_time - self.last_refresh > 300 or not self.recent_items:
            self.refresh_history(limit)
            self.last_refresh = current_time
        return self.recent_items

    def refresh_history(self, limit):
        """Fetch recent history embeddings and timestamps"""
        try:
            collection = Collection(HISTORY_COLLECTION_SECOND)
            collection.load()
            results = collection.query(
                expr="",
                output_fields=["embedding", "timestamp"],
                sort_by="timestamp",
                sort_descending=True,
                limit=limit
            )
            self.recent_items = [(np.array(item['embedding']), item['timestamp'])
                                 for item in results]
            return [emb for emb, _ in self.recent_items]
        except Exception as e:
            print(f"History refresh failed: {e}")
            return []

