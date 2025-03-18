import logging

from src.settings import LOG_FMT, LOG_LVL
from src.serpapi import SerpApiClient

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

__all__ = [
    "SerpApiClient",
]