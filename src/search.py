from copy import deepcopy
import json
import logging
import os
from typing import List, Dict, Any, Callable

import aiohttp

logger = logging.getLogger(__name__)


class SerpApi:
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


class DataForSeoApi:
    """A client to interact with the DataforSEO API for enhancing searches."""
    
    _max_retries = 3
    _retry_delay = 2
    _suggestions_endpoint = "/v3/dataforseo_labs/google/keyword_suggestions/live"
    _keywords_endpoint = "/v3/dataforseo_labs/google/related_keywords/live"

### --- CONTINUE FROM HERE ---

    def request(self, path, method, data=None):
        """Make a request to the DataforSEO API

        Args:
            path (str): path to the API endpoint
            method (str): HTTP method
            data (str): data to send with the request

        Returns:
            dict with the response from the API"""

        connection = HTTPSConnection("api.dataforseo.com")
        try:
            base64_bytes = b64encode(
                (
                    "%s:%s"
                    % (
                        os.getenv("DATAFORSEO_USER", "YOUR_DATAFORSEO_USERNAME"),
                        # self.context.settings.data_for_seo.username,
                        os.getenv("DATAFORSEO_PWD", "YOUR_DATAFORSEO_PASSWORD"),
                        # self.context.settings.data_for_seo.password,
                    )
                ).encode("ascii")
            ).decode("ascii")
            headers = {
                "Authorization": "Basic %s" % base64_bytes,
                "Content-Encoding": "gzip",
            }
            connection.request(method, path, headers=headers, body=data)
            response = connection.getresponse()
            if response.status >= 400:
                raise Exception(
                    f"Failed to call dataforseo: {response.status} {response.reason}"
                )
            return json.loads(response.read().decode())
        finally:
            connection.close()

    def get(self, path):
        return self.request(path, "GET")

    def post(self, path, data):
        if isinstance(data, str):
            data_str = data
        else:
            data_str = json.dumps(data)
        return self.request(path, "POST", data_str)

    def get_keyword_suggestions(self, keyword, location_name, language_name, limit=100):
        """Get keyword suggestions for a given keyword, location and language

        Args:
            keyword (str): keyword to get suggestions for
            location_name (str): location name
            language_name (str): language name
            limit (int): limit of suggestions to get

        Returns:
            list of dictionaries with keyword, volume, location and language
        """
        post_data = dict()
        post_data[len(post_data)] = dict(
            keyword=keyword,
            location_name=location_name,
            language_name=language_name,
            include_serp_info=True,
            include_seed_keyword=True,
            limit=limit,
        )
        response = self.post(
            "/v3/dataforseo_labs/google/keyword_suggestions/live", post_data
        )
        if response is None:
            return None
        else:
            keywords = []
            for task in response["tasks"]:
                if "result" in task:
                    for result in task["result"]:
                        if "items" in result:
                            for item in result["items"]:
                                keyword = item["keyword"]
                                search_volume = item["keyword_info"]["search_volume"]
                                keywords.append(
                                    {
                                        "keywordEnriched": keyword,
                                        "keywordLocation": location_name,
                                        "keywordLanguage": language_name,
                                        "keywordVolume": search_volume,
                                        "offerRoot": "KEYWORD_SUGGESTION",
                                    }
                                )
            return keywords

    def get_related_keywords(self, keyword, location_name, language_name, limit=100):
        """Get related keywords for a given keyword, location and language

        Args:
            keyword (str): keyword to get suggestions for
            location_name (str): location name
            language_name (str): language name
            limit (int): limit of suggestions to get

        Returns:
            list of tuples with keyword and search volume"""
        post_data = dict()
        post_data[len(post_data)] = dict(
            keyword=keyword,
            location_name=location_name,
            language_name=language_name,
            limit=limit,
        )
        response = self.post(
            "/v3/dataforseo_labs/google/related_keywords/live", post_data
        )
        if response is None:
            return None
        else:
            keywords = []
            for task in response["tasks"]:
                if "result" in task:
                    for result in task["result"]:
                        if "items" in result:
                            for item in result["items"]:
                                keyword = item["keyword_data"]["keyword"]
                                search_volume = item["keyword_data"]["keyword_info"][
                                    "search_volume"
                                ]
                                keywords.append(
                                    {
                                        "keywordEnriched": keyword,
                                        "keywordLocation": location_name,
                                        "keywordLanguage": language_name,
                                        "keywordVolume": search_volume,
                                        "offerRoot": "RELATED_KEYWORD",
                                    }
                                )

            return keywords


class KeywordEnricher:
    pass

class Search:


    
    async def apply():
        pass
