import logging
import os

def setup_logger() -> logging.Logger:
    """
    Nastaví logger který zapisuje do konzole i do souboru.
    """
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("route_weather")
    logger.setLevel(logging.DEBUG)

    # Formát zpráv
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1) Zapisuje do souboru
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 2) Zapisuje do konzole
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()