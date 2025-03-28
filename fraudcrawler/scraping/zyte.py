import asyncio
import logging

import aiohttp

from fraudcrawler.base.settings import MAX_RETRIES, RETRY_DELAY, ZYTE_PROBABILITY_THRESHOLD
from fraudcrawler.base.base import AsyncClient

logger = logging.getLogger(__name__)


class ZyteApi(AsyncClient):
    """A client to interact with the Zyte API for fetching product details."""

    _endpoint = "https://api.zyte.com/v1/extract"
    _config = {
        # "javascript": False,
        # "browserHtml": False,
        # "screenshot": False,
        # "productOptions": {"extractFrom": "httpResponseBody"},
        # "httpResponseBody": True,
        # "actions": [],
        "geolocation": "CH",
        "viewport": {"width": 1280, "height": 1080},
        "product": True,
    }

    def __init__(
        self,
        api_key: str,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
    ):
        """Initializes the ZyteApiClient with the given API key and retry configurations.

        Args:
            api_key: The API key for Zyte API.
            max_retries: Maximum number of retries for API calls.
            retry_delay: Delay between retries in seconds.
        """
        self._aiohttp_basic_auth = aiohttp.BasicAuth(api_key)
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def get_details(self, url: str) -> dict:
        """Fetches product details for a single URL.

        Args:
            url: The URL to fetch product details from.
        
        Returns:
            A dictionary containing the product details, fields include:
            (c.f. https://docs.zyte.com/zyte-api/usage/reference.html#operation/extract/response/200/product)
            {
                "url": str,
                "statusCode": str,
                "product": {
                    "name": str,
                    "price": str,
                    "mainImage": {"url": str},
                    "images": [{"url": str}],
                    "description": str,
                    "metadata": {
                        "probability": float,
                    },
                }
            }
        """
        logger.info(f"Fetching product details by Zyte for URL {url}.")
        attempts = 0
        err = None
        while attempts < self._max_retries:
            try:
                logger.debug(
                    f"Fetch product details for URL {url} (Attempt {attempts + 1})."
                )
                product = await self.post(
                    url=self._endpoint,
                    data={"url": url, **self._config},
                    auth=self._aiohttp_basic_auth,
                )
                return product
            except Exception as e:
                logger.debug(
                    f"Exception occurred while fetching product details for URL {url} (Attempt {attempts + 1})."
                )
                err = e
            attempts += 1
            if attempts < self._max_retries:
                await asyncio.sleep(self._retry_delay)
        if err is not None:
            raise err

    @staticmethod
    def keep_product(details: dict, threshold: float = ZYTE_PROBABILITY_THRESHOLD) -> bool:
        """Determines whether to keep the product based on the probability threshold.

        Args:
            details: A product details data dictionary.
            threshold: The probability threshold used to filter the products.
        """
        try:
            prob = float(details['product']['metadata']['probability'])
        except KeyError:
            logger.warning(f"Product with url={details.get('url')} has no probability value - product is ignored")
            return False
        return prob > threshold
