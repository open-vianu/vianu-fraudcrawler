import pytest

from src.base import Setup
from src.search import SerpApi

@pytest.fixture
def serpapi_client():
    setup = Setup()
    serpapi_client = SerpApi(api_key=setup.serpapi_key)
    return serpapi_client

@pytest.mark.asyncio
async def test_search(serpapi_client):
    search_term = "sildenafil"
    num_results = 5
    urls = await serpapi_client.search(search_term=search_term, num_results=num_results)
    assert len(urls) <= num_results
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)
