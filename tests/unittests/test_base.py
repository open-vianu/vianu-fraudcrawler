import logging

from src.settings import LOG_FMT, LOG_LVL
from src.base import Setup

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

def test_setup():
    setup = Setup()
    assert setup.serpapi_key
    assert setup.dataforseo_user
    assert setup.dataforseo_pwd
    assert setup.zyteapi_key
    assert setup.openaiapi_key