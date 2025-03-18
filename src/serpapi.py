from copy import deepcopy
import logging
from typing import List, Dict, Any, Callable

import aiohttp
import requests

logger = logging.getLogger(__name__)


class SerpApiClient:
    """A client to interact with the SerpApi for performing searches."""

    _endpoint = "https://serpapi.com/search"
    _engine = "google"

    def __init__(self, api_key: str, location: str = "Switzerland"):
        """Initializes the SerpApiClient with the given API key.

        Args:
            api_key: The API key for SerpApi.
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

    @staticmethod
    async def _aiohttp_get(
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Get the content of a given URL by an aiohttp GET request."""
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url=url, params=params) as response:
                response.raise_for_status()
                json_ = await response.json()
        return json_
    
    async def search(self, search_term: str, num_results: int = 10) -> List[str]:
        """Performs a search using SerpApi and returns the URLs of the results.

        Args:
            search_term: The search term to use for the query.
            num_results: Max number of results to return (default: 10).
        """
        # Setup the parameters
        logger.info(f'Performing SerpAPI search for search_term="{search_term}".')
        params = deepcopy(self._base_config)
        params["q"] = search_term
        params["num"] = num_results

        # Perform the request
        data = await self._aiohttp_get(url=self._endpoint, params=params)

        # Extract the URLs from the response
        results = data.get("organic_results", [])
        urls = [res.get("link") for res in results]
        logger.info(f"Found {len(urls)} URLs from SerpApi search.")
        return urls

    # @staticmethod
    # def _check_limit(urls: List[str], query: str, limit: int = 200) -> List[str]:
    #     """
    #     Checks if the number of URLs exceeds the limit, and trims the list if necessary.

    #     Args:
    #         urls (List[str]): The list of URLs.
    #         query (str): The search query.
    #         limit (int): hight of limit

    #     Returns:
    #         List[str]: The potentially trimmed list of URLs.
    #     """
    #     if len(urls) > limit:
    #         urls = urls[:limit]
    #         logger.warning(f"Reached limit for keyword: {query}")
    #     return urls

    # def call_serpapi(
    #     self,
    #     params: Dict[str, Any],
    #     log_name: str,
    #     callback: Callable[int, None] | None = None,
    # ) -> Dict[str, Any]:
    #     """
    #     Calls the SerpAPI and returns the response, with optional caching.

    #     Args:
    #         params (Dict[str, Any]): Parameters for the API call.
    #         log_name (str): The name used for logging.
    #         force_refresh (bool): Whether to bypass the cache and force a new API call (default is False).

    #     Raises:
    #         Exception: If all API call attempts fail.
    #     """
    #     import time
    #     attempts = 0
    #     max_retries = 5
    #     retry_delay = 5
    #     while attempts < max_retries:
    #         try:
    #             # search = GoogleSearch(params)
    #             # response = search.get_response()
    #             response = requests.get(
    #                 url=self._endpoint,
    #                 params=params,
    #                 timeout=self._requests_timeout,
    #             )
    #             response.raise_for_status()
    #             if callback is not None:
    #                 callback(1)
    #             return response.json()
    #         except Exception as e:
    #             logger.warning(
    #                 f"API call failed with error: {e}. Retrying in {retry_delay} seconds..."
    #             )
    #             attempts += 1
    #             time.sleep(retry_delay)
    #     raise Exception("All API call attempts to SerpAPI failed.")