import json
import os
import re
import logging
from typing import List, Dict
from datetime import datetime
from backend.utils.config import ERROR_LOG_PATH, JSON_URL
from pymilvus import connections, Collection, MilvusException
from elasticsearch import Elasticsearch
from backend.utils.config import MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, ES_HOST, ES_PORT, ES_INDEX

logger = logging.getLogger()
def load_all_documents() -> List[dict]:
    with open(JSON_URL, "r", encoding="utf-8") as f:
        return json.load(f)

def get_source_file_count() -> int:
    return len(load_all_documents())

def get_milvus_count():
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        collection = Collection(COLLECTION_NAME)
        if not collection.has_index():
            logger.warning("Milvus collection exists but has no index")
        return collection.num_entities
    except MilvusException as e:
        logger.error(f"Milvus connection error: {str(e)}")
        return -1

def get_es_count():
    try:
        es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}", verify_certs=False)
        count = es.count(index=ES_INDEX)['count']
        logger.info(f"Successfully retrieved Elasticsearch count: {count}")
        return count
    except Exception as e:
        logger.error(f"Error getting Elasticsearch count: {str(e)}")
        return -1


def get_dataset_info() -> Dict[str, any]:
    try:
        collection = Collection(COLLECTION_NAME)
        collection.load()

        total = collection.num_entities

        def get_distinct_values(field: str, limit: int = 1000) -> List[str]:
            results = collection.query(
                expr=f"{field} != ''",
                output_fields=[field],
                limit=limit
            )
            return sorted({item[field] for item in results if field in item})

        return {
            "total": total,
            "types": get_distinct_values("type"),
            "categories": get_distinct_values("category")
        }

    except Exception as e:
        logger.error(f"Error getting dataset info: {str(e)}")
        return {
            "total": 0,
            "types": [],
            "categories": []
        }

def get_recent_errors(limit=10):
    if not os.path.exists(ERROR_LOG_PATH):
        return []
    try:
        errors = []
        with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_error = None

        for line in reversed(lines[-1000:]):  # Only check last 1000 lines for performance
            line = line.strip()
            if not line:
                continue
            timestamp_match = re.match(
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \[(ERROR|CRITICAL|WARNING)\] (.+)', line)

            if timestamp_match:
                if current_error and len(errors) < limit:
                    errors.append(current_error)

                timestamp_str, level, message = timestamp_match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f").isoformat()
                except ValueError:
                    timestamp = timestamp_str

                current_error = {
                    "id": f"error-{len(errors) + 1}",
                    "timestamp": timestamp,
                    "level": level,
                    "message": message
                }
            else:
                if current_error:
                    current_error["message"] += "\n" + line

        if current_error and len(errors) < limit:
            errors.append(current_error)

        return errors[:limit]

    except Exception as e:
        logger.error(f"Error reading error log: {str(e)}")
        return [{
            "id": "system-error",
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": f"Failed to read error log: {str(e)}"
        }]
