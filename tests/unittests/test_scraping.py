import pytest

from fraudcrawler.base.base import Setup, Keyword, Host, Location, Language
from fraudcrawler import SerpApi, Enricher, ZyteApi


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


@pytest.fixture
def zyteapi():
    setup = Setup()
    zyteapi = ZyteApi(api_key=setup.zyteapi_key)
    return zyteapi


@pytest.mark.asyncio
async def test_serpapi_search(serpapi):
    search_string = "sildenafil"
    location = Location(name="Switzerland", code="ch")
    num_results = 5
    urls = await serpapi._search(
        search_string=search_string,
        location=location,
        num_results=num_results,
    )
    assert 0 < len(urls) <= num_results
    assert all(isinstance(url, str) for url in urls)
    assert all(url.startswith("http") for url in urls)


def test_serpapi_keep_url(serpapi):
    assert serpapi._keep_url(url="https://example.ch", country_code='ch') is True
    assert serpapi._keep_url(url="https://example.ch/foobar", country_code='ch') is True
    assert serpapi._keep_url(url="https://example.com", country_code='ch') is True
    assert serpapi._keep_url(url="https://example.it", country_code='ch') is False


@pytest.mark.asyncio
async def test_serpapi_apply_marketplaces(serpapi):
    search_term = "sildenafil"
    location = Location(name="Switzerland", code="ch")
    marketplaces = [Host(name="Ricardo", domains="ricardo.ch")]
    num_results = 5
    urls = await serpapi.apply(
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
    urls = await serpapi.apply(
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


@pytest.mark.asyncio
async def test_zyteapi_get_results(zyteapi):
    url = "https://www.altibbi.com/answer/159"
    product = await zyteapi.get_details(url=url)
    assert product
    assert product.get("url") == url
    assert 'product' in product
    assert 'metadata' in product['product']
