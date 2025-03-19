import logging
import pytest

from src.settings import LOG_FMT, LOG_LVL
from src.base import Setup
from src.search import SerpApi, DataForSeoApi, Keyword

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

@pytest.fixture
def serpapi_client():
    setup = Setup()
    serpapi_client = SerpApi(api_key=setup.serpapi_key)
    return serpapi_client

@pytest.fixture
def dataforseo_api():
    setup = Setup()
    dataforseo_api = DataForSeoApi(
        user=setup.dataforseo_user,
        pwd=setup.dataforseo_pwd,
    )
    return dataforseo_api

@pytest.mark.asyncio
async def test_search(serpapi_client):
    search_term = "sildenafil"
    num_results = 5
    urls = await serpapi_client.search(search_term=search_term, num_results=num_results)
    assert 0 < len(urls) <= num_results
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)

@pytest.mark.asyncio
async def test_dataforseo_suggested_keywords(dataforseo_api):
    search_term = "sildenafil"
    location = "Switzerland"
    language = "German"
    limit = 5
    keywords = await dataforseo_api.get_suggested_keywords(
        search_term=search_term,
        location=location,
        language=language,
        limit=limit,
    )
    assert 0 < len(keywords) <= limit
    assert all(isinstance(kw, Keyword) for kw in keywords)


@pytest.mark.asyncio
async def test_dataforseo_related_keywords(dataforseo_api):
    search_term = "sildenafil"
    location = "Switzerland"
    language = "German"
    limit = 5
    keywords = await dataforseo_api.get_related_keywords(
        search_term=search_term,
        location=location,
        language=language,
        limit=limit,
    )
    assert 0 < len(keywords) <= limit
    assert all(isinstance(kw, Keyword) for kw in keywords)
