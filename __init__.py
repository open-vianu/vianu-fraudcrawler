import logging

from src.settings import LOG_FMT, LOG_LVL
from src.search import SerpApi, DataForSeoApi, Search

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

__all__ = [
    "SerpApi",
    "DataForSeoApi",
    "Search",
]