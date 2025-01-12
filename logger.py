import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("ParserLogger")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    "parser.log", maxBytes=1_000_000_000, backupCount=5, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
