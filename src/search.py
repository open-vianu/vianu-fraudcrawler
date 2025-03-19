from base64 import b64encode
from copy import deepcopy
import logging
from pydantic import BaseModel
from typing import List, Iterator

import aiohttp

from src.settings import ENRICHMENT_UPPER_LIMIT

logger = logging.getLogger(__name__)


class AsyncClient:

    @staticmethod
    async def get(
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Async GET request of a given URL returning the data."""
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url=url, params=params) as response:
                response.raise_for_status()
                json_ = await response.json()
        return json_
    
    @staticmethod
    async def post(
        url: str,
        headers: dict | None = None,
        data: dict | None = None,
    ) -> dict:
        """Async POST request of a given URL returning the data."""
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url=url, json=data) as response:
                response.raise_for_status()
                json_ = await response.json()
        return json_


class SerpApi(AsyncClient):
    """A client to interact with the SerpApi for performing searches."""

    _endpoint = "https://serpapi.com/search"
    _engine = "google"

    def __init__(self, api_key: str, location: str = "Switzerland"):
        """Initializes the SerpApiClient with the given API key.

        Args:
            api_key: The API key for SerpApi.
            location: The location to use for the search (default: "Switzerland").
        """
        super().__init__()
        self._api_key = api_key
        self._location = location
        self._base_config = {
            "engine": self._engine,
            "api_key": api_key,
            "location_requested": self._location,
            "location_used": self._location,
        }

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
        try:
            response = await self.get(url=self._endpoint, params=params)
        except Exception as e:
            logger.error(f'SerpAPI search failed with error: {e}.')

        # Extract the URLs from the response
        results = response.get("organic_results", [])
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



class Keyword(BaseModel):
    text: str
    volume: int


class DataForSeoApi(AsyncClient):
    """A client to interact with the DataForSEO API for enhancing searches."""
    
    _auth_encoding = 'ascii'
    _max_retries = 3
    _retry_delay = 2
    _base_endpoint = "https://api.dataforseo.com"
    _suggestions_endpoint = "/v3/dataforseo_labs/google/keyword_suggestions/live"
    _keywords_endpoint = "/v3/dataforseo_labs/google/related_keywords/live"

    def __init__(self, user: str, pwd: str):
        """Initializes the DataForSeoApiClient with the given username and password.

        Args:
            user: The username for DataForSEO API.
            pwd: The password for DataForSEO API.
        """
        self._user = user
        self._pwd = pwd
        auth = f"{user}:{pwd}"
        auth = b64encode(auth.encode(self._auth_encoding)).decode(self._auth_encoding)
        self._headers = {
            "Authorization": f"Basic {auth}",
            "Content-Encoding": "gzip",
        }

    @staticmethod
    def _extract_items_from_data(data: dict) -> Iterator[dict]:
        """Extracts the items from the DataForSEO response.
        
        Args:
            data: The response data from DataForSEO.
        """
        tasks = data.get("tasks") or []  # in contrast to data.get("tasks", []) this handles the case where data["tasks"] is set to None
        for task in tasks:
            results = task.get("result") or []
            for result in results:
                items = result.get("items") or []
                yield from items

    @staticmethod
    def _parse_suggested_keyword(item: dict) -> Keyword:
        """Parses a keyword from an item in the DataForSEO suggested keyword search response.

        Args:
            item: An item from the DataForSEO response.
        """
        text = item["keyword"]
        volume = item["keyword_info"]["search_volume"]
        return Keyword(text=text, volume=volume)

    def _extract_suggested_keywords(self, data: dict) -> List[Keyword]:
        """Extracts the keywords from the DataForSEO response for suggested keywords.

        Args:
            data: The response data from DataForSEO.

        The DataForSEO results are of the form
        (c.f. https://docs.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live/?bash):
        {
          "tasks": [
            {
              "result": [
                {
                  "items": [
                    {
                      "keyword": <suggested-keyword>,
                      "keyword_info": {
                        "search_volume": <volume>
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }

        Args:
            data: The response data from DataForSEO.
        """
        keywords = []
        for item in self._extract_items_from_data(data=data):
            try:
                keyword = self._parse_suggested_keyword(item)
                keywords.append(keyword)
            except Exception as e:
                logger.warning(f"Ignoring keyword due to error: {e}.")
        return keywords

    async def get_suggested_keywords(
        self,
        search_term: str,
        location: str,
        language: str,
        limit: int = ENRICHMENT_UPPER_LIMIT,
    ) -> List[Keyword]:
        """Get keyword suggestions for a given search_term.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the search.
            language: The language to use for the search.
            limit: The upper limit of suggestions to get.
        """
        data = [
            {
                "keyword": search_term,
                "location_name": location,
                "language_name": language,
                "limit": limit,
                "include_serp_info": True,
                "include_seed_keyword": True,
            }
        ]
        logger.info(f'DataForSEO search for suggested keywords with search_term="{search_term}".')
        try:
            url = f"{self._base_endpoint}{self._suggestions_endpoint}"
            logger.debug(f'DataForSEO url="{url}" with data="{data}".')
            sugg_data = await self.post(url=url, headers=self._headers, data=data)
        except Exception as e:
            logger.error(f'DataForSEO suggested search failed with error: {e}.')

        # Extract the keywords from the response
        try:
            keywords = self._extract_suggested_keywords(data=sugg_data)
        except Exception as e:
            logger.error(f'Failed to extract suggested keywords from DataForSEO response with error: {e}.')
        
        logger.info(f"Found {len(keywords)} suggestions from DataForSEO search.")
        return keywords
    
    @staticmethod
    def _parse_related_keyword(item: dict) -> Keyword:
        """Parses a keyword from an item in the DataForSEO related keyword search response.

        Args:
            item: An item from the DataForSEO response.
        """
        text = item["keyword_data"]["keyword"]
        volume = item["keyword_data"]["keyword_info"]["search_volume"]
        return Keyword(text=text, volume=volume)

    def _extract_related_keywords(self, data: dict) -> List[Keyword]:
        """Extracts the keywords from the DataForSEO response for related keywords.

        Args:
            data: The response data from DataForSEO.

        The DataForSEO results are of the form
        (c.f. https://docs.dataforseo.com/v3/dataforseo_labs/google/related_keywords/live/?bash):
        {
          "tasks": [
            {
              "result": [
                {
                  "items": [
                    {
                      "keyword_data": {
                        "keyword": <related-keyword>,
                        "keyword_info": {
                          "search_volume": <volume>
                        }
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }

        Args:
            data: The response data from DataForSEO.
        """
        keywords = []
        for item in self._extract_items_from_data(data=data):
            try:
                keyword = self._parse_related_keyword(item)
                keywords.append(keyword)
            except Exception as e:
                logger.warning(f"Ignoring keyword due to error: {e}.")
        return keywords

    async def get_related_keywords(
        self,
        search_term: str,
        location: str,
        language: str,
        limit: int = ENRICHMENT_UPPER_LIMIT,
    ) -> List[Keyword]:
        """Get related keywords for a given search_term.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the search.
            language: The language to use for the search.
            limit: The upper limit of suggestions to get.
        """
        data = [
            {
                "keyword": search_term,
                "location_name": location,
                "language_name": language,
                "limit": limit,
            }
        ]
        logger.info(f'DataForSEO search for related keywords with search_term="{search_term}".')
        try:
            url = f"{self._base_endpoint}{self._keywords_endpoint}"
            logger.debug(f'DataForSEO url="{url}" with data="{data}".')
            rel_data = await self.post(url=url, headers=self._headers, data=data)
        except Exception as e:
            logger.error(f'DataForSEO related keyword search failed with error: {e}.')

        # Extract the keywords from the response
        try:
            keywords = self._extract_related_keywords(data=rel_data)
        except Exception as e:
            logger.error(f'Failed to extract related keywords from DataForSEO response with error: {e}.')
        
        logger.info(f"Found {len(keywords)} related keywords from DataForSEO search.")
        return keywords


class KeywordEnricher:
    pass

class Search:
    async def apply():
        pass
