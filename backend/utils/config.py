import yaml
import os
import socket

def load_config(path="../../config.yml"):
    absolute_path = os.path.abspath(os.path.join(os.path.dirname(__file__), path))
    with open(absolute_path, "r") as file:
        config = yaml.safe_load(file)

    # Get actual host IP once
    host_ip = socket.gethostbyname(socket.gethostname())

    # Replace the placeholder in kafka broker if present
    kafka_broker = config.get("kafka", {}).get("kafka_broker", "")
    if "{HOST_IP}" in kafka_broker:
        config["kafka"]["kafka_broker"] = kafka_broker.replace("{HOST_IP}", host_ip)

    return config


config = load_config()

MODEL = config["model"]["model_name"]

JSON_URL = config["json"]["json_url"]
QUERY_JSON_URL = config["json"]["query_json_url"]

SEARCH_API = config["api"]["search_url"]
UPSERT_API = config["api"]["upsert_url"]
ADMIN_API = config["api"]["admin_url"]
HISTORY_API = config["api"]["history_url"]

MILVUS_HOST = config["milvus"]["MILVUS_HOST"]
MILVUS_PORT = config["milvus"]["MILVUS_PORT"]
COLLECTION_NAME = config["milvus"]["collection_name"]

KAFKA_BROKER = config["kafka"]["kafka_broker"]

ERROR_LOG_PATH = config["log"]["error_log"]
UPSERT_LOG_PATH = config["log"]["upsert_log"]

ES_HOST = "http://localhost:9200"
ES_PORT = config["es"]["es_port"]
ES_INDEX = config["es"]["es_index"]
