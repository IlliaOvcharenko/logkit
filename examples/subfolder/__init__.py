from logkit.core import get_logger
logger = get_logger("my_app", __name__, propagate=True)


def log_smth():
    for i in range(3):
        logger.info(f"number {i}")
