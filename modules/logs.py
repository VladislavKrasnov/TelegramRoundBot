import logging
import os

def setup_logging(logs_path: str):
    logs_dir = os.path.dirname(logs_path)
    if logs_dir and not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except OSError as e:
            print(f"Could not create logs directory {logs_dir}: {e}")

    logging.basicConfig(
        filename=logs_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
        encoding='utf-8'
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully.")

