from base64 import b64encode
import logging
from typing import List, Iterator

from fraudcrawler.base.settings import ENRICHMENT_UPPER_LIMIT
from fraudcrawler.base.base import Location, Language, Keyword, AsyncClient


logger = logging.getLogger(__name__)


class Enricher(AsyncClient):
    """A client to interact with the DataForSEO API for enhancing searches (producing alternative search_terms)."""

    _auth_encoding = "ascii"
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
        tasks = (
            data.get("tasks") or []
        )  # in contrast to data.get("tasks", []) this handles the case where data["tasks"] is set to None
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

    async def _get_suggested_keywords(
        self,
        search_term: str,
        language: Language,
        location: Location,
        limit: int = ENRICHMENT_UPPER_LIMIT,
    ) -> List[Keyword]:
        """Get keyword suggestions for a given search_term.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the search.
            language: The language to use for the search.
            limit: The upper limit of suggestions to get.
        """

        # Data must be a list of dictionaries setting a number of search tasks; here we only have one task.
        data = [
            {
                "keyword": search_term,
                "language_name": language.name,
                "location_name": location.name,
                "limit": limit,
                "include_serp_info": True,
                "include_seed_keyword": True,
            }
        ]
        logger.debug(
            f'DataForSEO search for suggested keywords with search_term="{search_term}".'
        )
        try:
            url = f"{self._base_endpoint}{self._suggestions_endpoint}"
            logger.debug(f'DataForSEO url="{url}" with data="{data}".')
            sugg_data = await self.post(url=url, headers=self._headers, data=data)
        except Exception as e:
            logger.error(f"DataForSEO suggested search failed with error: {e}.")

        # Extract the keywords from the response
        try:
            keywords = self._extract_suggested_keywords(data=sugg_data)
        except Exception as e:
            logger.error(
                f"Failed to extract suggested keywords from DataForSEO response with error: {e}."
            )

        logger.debug(f"Found {len(keywords)} suggestions from DataForSEO search.")
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

    async def _get_related_keywords(
        self,
        search_term: str,
        language: Language,
        location: Location,
        limit: int = ENRICHMENT_UPPER_LIMIT,
    ) -> List[Keyword]:
        """Get related keywords for a given search_term.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the search.
            language: The language to use for the search.
            limit: The upper limit of suggestions to get.
        """

        # Data must be a list of dictionaries setting a number of search tasks; here we only have one task.
        data = [
            {
                "keyword": search_term,
                "language_name": language.name,
                "location_name": location.name,
                "limit": limit,
            }
        ]
        logger.debug(
            f'DataForSEO search for related keywords with search_term="{search_term}".'
        )
        try:
            url = f"{self._base_endpoint}{self._keywords_endpoint}"
            logger.debug(f'DataForSEO url="{url}" with data="{data}".')
            rel_data = await self.post(url=url, headers=self._headers, data=data)
        except Exception as e:
            logger.error(f"DataForSEO related keyword search failed with error: {e}.")

        # Extract the keywords from the response
        try:
            keywords = self._extract_related_keywords(data=rel_data)
        except Exception as e:
            logger.error(
                f"Failed to extract related keywords from DataForSEO response with error: {e}."
            )

        logger.debug(f"Found {len(keywords)} related keywords from DataForSEO search.")
        return keywords

    async def apply(
        self,
        search_term: str,
        language: Language,
        location: Location,
        n_terms: int,
    ) -> List[str]:
        """Applies the enrichment to a search_term.

        Args:
            search_term: The search term to use for the query.
            location: The location to use for the search.
            language: The language to use for the search.
            n_terms: The number of additional terms
        """
        # Get the additional keywords

        logger.info(
            f'Applying enrichment for search_term="{search_term}" and n_terms="{n_terms}".'
        )
        suggested = await self._get_suggested_keywords(
            search_term=search_term,
            location=location,
            language=language,
            limit=n_terms,
        )
        related = await self._get_related_keywords(
            search_term=search_term,
            location=location,
            language=language,
            limit=n_terms,
        )

        # TODO continue from here
        #  - filter out the blacklisted search terms (c.f. utils)
        #  - aggregate the keywords (sum the volumes for duplicates)
        #    Q: WHY ARE THE KEYWORDS OF DIFFERENT LANGUAGES AND LOCATIONS IN THE OLD VERSION???
        #  - sort the keywords by volume
        #  - search for the terms with SerpApi
        #  - aggregate the urls (sum the volumes for duplicates)
        #    Q: IS THIS REALLY NECESSARY? WHY NOT JUST RETURN THE URLS?

        # TODO
        #  - use Location and Language models

        # Combine the keywords and sort them by volume
        keywords = suggested + related
        keywords = sorted(keywords, key=lambda kw: kw.volume, reverse=True)
        terms = [kw.text for kw in keywords[:n_terms]]
        logger.info(f"Found {len(terms)} additional terms.")
        return terms
