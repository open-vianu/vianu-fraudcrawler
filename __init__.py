import logging

from src.settings import LOG_FMT, LOG_LVL
from src import base
from src import collect

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

__all__ = [
    "base",
    "collect",
]