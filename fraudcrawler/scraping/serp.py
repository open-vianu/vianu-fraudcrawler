import asyncio
import logging
from typing import List
from urllib.parse import urlparse

from fraudcrawler.base.settings import MAX_RETRIES, RETRY_DELAY
from fraudcrawler.base.base import Host, Location, AsyncClient

logger = logging.getLogger(__name__)


class SerpApi(AsyncClient):
    """A client to interact with the SerpApi for performing searches."""

    _endpoint = "https://serpapi.com/search"
    _engine = "google"

    def __init__(
        self,
        api_key: str,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
    ):
        """Initializes the SerpApiClient with the given API key.

        Args:
            api_key: The API key for SerpApi.
            max_retries: Maximum number of retries for API calls.
            retry_delay: Delay between retries in seconds.
        """
        super().__init__()
        self._api_key = api_key
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    @staticmethod
    def _get_hostname(url: str) -> str | None:
        """Extracts the hostname together with the top-level domain in the form `hostname.tld.

        Args:
            url: The URL to be processed.

        """
        # Add scheme (if needed -> urlparse requires it)
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        # Get the hostname
        hostname = urlparse(url).hostname

        # Remove 'www' subdomain
        if hostname and hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    async def search(
        self,
        search_term: str,
        location: Location,
        num_results: int,
        marketplaces: List[Host] | None = None,
        excluded_urls: List[Host] | None = None,
    ) -> List[str]:
        """Performs a search using SerpApi and returns the URLs of the results.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the query.
            num_results: Max number of results to return (default: 10).
            marketplaces: The marketplaces to include in the search.
            excluded_urls: The URLs to exclude from the search.
        """
        # Setup the parameters
        logger.info(f'Performing SerpAPI search for search_term="{search_term}".')

        # Setup the parameters
        #  - q: The search term (with potentially added site: parameters for marketplaces).
        #  - location_[requested|used]: The location to use for the search.
        #  - google_domain: The Google domain to use for the search (e.g. google.[com]).
        #  - num: The number of results to return.
        #  - engine: The search engine to use ('google' NOT 'google_shopping').
        search_string = search_term
        if marketplaces:
            sites = [dom for host in marketplaces for dom in host.domains]
            search_string += " site:" + " OR site:".join(s for s in sites)
        params = {
            "q": search_string,
            "location_requested": location.name,
            "location_used": location.name,
            "google_domain": f"google.{location.code}",
            "num": num_results,
            "engine": self._engine,
            "api_key": self._api_key,
        }

        # Perform the request
        attempts = 0
        err = None
        while attempts < self._max_retries:
            try:
                logger.debug(
                    f'Performing SerpAPI search with q="{search_string}" (Attempt {attempts + 1}).'
                )
                response = await self.get(url=self._endpoint, params=params)
                break
            except Exception as e:
                logger.error(f"SerpAPI search failed with error: {e}.")
                err = e
            attempts += 1
            if attempts < self._max_retries:
                await asyncio.sleep(self._retry_delay)
        if err is not None:
            raise err

        # Extract the URLs from the response
        results = response.get("organic_results", [])
        urls = [res.get("link") for res in results]
        logger.debug(
            f'Found {len(urls)} URLs from SerpApi search for q="{search_string}".'
        )

        # Filter out the excluded URLs
        if excluded_urls:
            excluded = [dom for excl in excluded_urls for dom in excl.domains]
            urls = [url for url in urls if self._get_hostname(url) not in excluded]
            logger.debug(
                f"Filtered down to {len(urls)} URLs after excluding given domains."
            )

        logger.info(
            f'Found {len(urls)} URLs from SerpApi search with q="{search_string}".'
        )
        return urls
