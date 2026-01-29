import logging

logger = logging.getLogger("telegram_bots")


def configure_logging(level=logging.INFO, fmt=None):
    """Configure logging for the bot."""

    if fmt is None:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    return logger
