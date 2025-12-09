import os
import logging
from backend_second.utils.config import ERROR_LOG_PATH, UPSERT_LOG_PATH

def setup_logger():
    # === Error Logger ===
    error_log_dir = os.path.dirname(ERROR_LOG_PATH)
    os.makedirs(error_log_dir, exist_ok=True)

    error_handler = logging.FileHandler(ERROR_LOG_PATH)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # === Upsert Logger ===
    upsert_log_dir = os.path.dirname(UPSERT_LOG_PATH)
    os.makedirs(upsert_log_dir, exist_ok=True)

    upsert_handler = logging.FileHandler(UPSERT_LOG_PATH)
    upsert_handler.setLevel(logging.INFO)
    upsert_handler.setFormatter(logging.Formatter("%(asctime)s [UPSERT] %(message)s"))

    # === Root Logger Setup ===
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(error_handler)
    logger.addHandler(upsert_handler)

    return logger
