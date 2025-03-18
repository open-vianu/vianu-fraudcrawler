from copy import deepcopy
import logging
from typing import List, Dict, Any, Callable

import requests

from src.settings import REQUESTS_TIMEOUT

logger = logging.getLogger(__name__)


class SerpApiClient:
    """A client to interact with the SERP API for performing searches."""

    _endpoint = "https://serpapi.com/search"
    _engine = "google"
    _requests_timeout = REQUESTS_TIMEOUT

    def __init__(self, api_key: str, location: str = "Switzerland"):
        """Initializes the SerpApiClient with the given API key.

        Args:
            api_key: The API key for SERP API.
            location: The location to use for the search (default: "Switzerland").
        """
        self._api_key = api_key
        self._location = location
        self._base_config = {
            "engine": self._engine,
            "api_key": api_key,
            "location_requested": self._location,
            "location_used": self._location,
        }

    def search(self, search_term: str, num_results: int = 10) -> List[str]:
        """Performs a search using SERP API and returns the URLs of the results.

        Args:
            search_term: The search term to use for the query.
            num_results: Max number of results to return (default: 10).
        """
        # Setup the parameters
        logger.info(f'Performing SERP API search for search_term "{search_term}".')
        params = deepcopy(self._base_config)
        params["q"] = search_term
        params["num"] = num_results

        # Perform the request
        response = requests.get(
            url=self._endpoint,
            params=params,
            timeout=self._requests_timeout,
        )

        # Handle the response
        status_code = response.status_code
        if status_code == 200:
            data = response.json()
            search_results = data.get("organic_results", [])
            urls = [result.get("link") for result in search_results]
            logger.info(f"Found {len(urls)} URLs from SERP API search.")
            return urls
        else:
            logger.error(f"SERP API request failed with status code {status_code}.")
            return []

    @staticmethod
    def _check_limit(urls: List[str], query: str, limit: int = 200) -> List[str]:
        """
        Checks if the number of URLs exceeds the limit, and trims the list if necessary.

        Args:
            urls (List[str]): The list of URLs.
            query (str): The search query.
            limit (int): hight of limit

        Returns:
            List[str]: The potentially trimmed list of URLs.
        """
        if len(urls) > limit:
            urls = urls[:limit]
            logger.warning(f"Reached limit for keyword: {query}")
        return urls

    def call_serpapi(
        self,
        params: Dict[str, Any],
        log_name: str,
        callback: Callable[int, None] | None = None,
    ) -> Dict[str, Any]:
        """
        Calls the SerpAPI and returns the response, with optional caching.

        Args:
            params (Dict[str, Any]): Parameters for the API call.
            log_name (str): The name used for logging.
            force_refresh (bool): Whether to bypass the cache and force a new API call (default is False).

        Raises:
            Exception: If all API call attempts fail.
        """
        import time
        attempts = 0
        max_retries = 5
        retry_delay = 5
        while attempts < max_retries:
            try:
                # search = GoogleSearch(params)
                # response = search.get_response()
                response = requests.get(
                    url=self._endpoint,
                    params=params,
                    timeout=self._requests_timeout,
                )
                response.raise_for_status()
                if callback is not None:
                    callback(1)
                return response.json()
            except Exception as e:
                logger.warning(
                    f"API call failed with error: {e}. Retrying in {retry_delay} seconds..."
                )
                attempts += 1
                time.sleep(retry_delay)
        raise Exception("All API call attempts to SerpAPI failed.")