import logging
import pytest

from src.settings import LOG_FMT, LOG_LVL
from src.base import Setup
from src.search import SerpApi, Enricher, Keyword

logging.basicConfig(level=LOG_LVL.upper(), format=LOG_FMT)
logger = logging.getLogger(__name__)

@pytest.fixture
def serpapi():
    setup = Setup()
    serpapi = SerpApi(api_key=setup.serpapi_key)
    return serpapi

@pytest.fixture
def enricher():
    setup = Setup()
    enricher = Enricher(
        user=setup.dataforseo_user,
        pwd=setup.dataforseo_pwd,
    )
    return enricher

@pytest.mark.asyncio
async def test_serpapi_search(serpapi):
    search_term = "sildenafil"
    location = "Switzerland"
    num_results = 5
    urls = await serpapi.search(
        search_term=search_term,
        location=location,
        num_results=num_results,
    )
    assert 0 < len(urls) <= num_results
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)

@pytest.mark.asyncio
async def test_enricher_get_suggested_keywords(enricher):
    search_term = "sildenafil"
    location = "Switzerland"
    language = "German"
    limit = 5
    keywords = await enricher.get_suggested_keywords(
        search_term=search_term,
        location=location,
        language=language,
        limit=limit,
    )
    assert 0 < len(keywords) <= limit
    assert all(isinstance(kw, Keyword) for kw in keywords)


@pytest.mark.asyncio
async def test_enricher_get_related_keywords(enricher):
    search_term = "sildenafil"
    location = "Switzerland"
    language = "German"
    limit = 5
    keywords = await enricher.get_related_keywords(
        search_term=search_term,
        location=location,
        language=language,
        limit=limit,
    )
    assert 0 < len(keywords) <= limit
    assert all(isinstance(kw, Keyword) for kw in keywords)


@pytest.mark.asyncio
async def test_enricher_apply(enricher):
    search_term = "sildenafil"
    location = "Switzerland"
    language = "German"
    n_terms = 5
    terms = await enricher.apply(
        search_term=search_term,
        location=location,
        language=language,
        n_terms=n_terms,
    )
    assert len(terms) == n_terms
    assert all(isinstance(t, str) for t in terms)
