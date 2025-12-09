import os
import logging
from backend.utils.config import ERROR_LOG_PATH, UPSERT_LOG_PATH

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # === Error Logger ===
    error_log_dir = os.path.dirname(ERROR_LOG_PATH)
    os.makedirs(error_log_dir, exist_ok=True)
    error_handler = logging.FileHandler(ERROR_LOG_PATH, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # === Upsert Logger ===
    upsert_log_dir = os.path.dirname(UPSERT_LOG_PATH)
    os.makedirs(upsert_log_dir, exist_ok=True)
    upsert_handler = logging.FileHandler(UPSERT_LOG_PATH, encoding='utf-8')
    upsert_handler.setLevel(logging.INFO)
    upsert_handler.setFormatter(logging.Formatter("%(asctime)s [UPSERT] %(message)s"))

    # === Console Logger (Optional) ===
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    logger.addHandler(error_handler)
    logger.addHandler(upsert_handler)
    logger.addHandler(stream_handler)

    return logger
