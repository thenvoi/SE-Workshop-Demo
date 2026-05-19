import logging


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger("thenvoi").setLevel(level)
