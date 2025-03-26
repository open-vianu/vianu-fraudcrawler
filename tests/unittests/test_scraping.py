import pytest

from fraudcrawler.base.base import Setup, Keyword, Host, Location, Language
from fraudcrawler.scraping.serp import SerpApi
from fraudcrawler.scraping.enrich import Enricher


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
    location = Location(name="Switzerland", code="ch")
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
async def test_serpapi_search_marketplaces(serpapi):
    search_term = "sildenafil"
    location = Location(name="Switzerland", code="ch")
    marketplaces = [Host(name="Ricardo", domains="ricardo.ch")]
    num_results = 5
    urls = await serpapi.search(
        search_term=search_term,
        location=location,
        num_results=num_results,
        marketplaces=marketplaces,
    )
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)


@pytest.mark.asyncio
async def test_serpapi_search_excluded_urls(serpapi):
    search_term = "sildenafil"
    location = Location(name="Switzerland", code="ch")
    excluded_urls = [Host(name="Altibbi", domains="altibbi.com")]
    num_results = 5
    urls = await serpapi.search(
        search_term=search_term,
        location=location,
        num_results=num_results,
        excluded_urls=excluded_urls,
    )
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)


@pytest.mark.asyncio
async def test_enricher_get_suggested_keywords(enricher):
    search_term = "sildenafil"
    location = Location(name="Switzerland", code="ch")
    language = Language(name="German", code="de")
    limit = 5
    keywords = await enricher._get_suggested_keywords(
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
    location = Location(name="Switzerland", code="ch")
    language = Language(name="German", code="de")
    limit = 5
    keywords = await enricher._get_related_keywords(
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
    location = Location(name="Switzerland", code="ch")
    language = Language(name="German", code="de")
    n_terms = 5
    terms = await enricher.apply(
        search_term=search_term,
        location=location,
        language=language,
        n_terms=n_terms,
    )
    assert len(terms) == n_terms
    assert all(isinstance(t, str) for t in terms)
