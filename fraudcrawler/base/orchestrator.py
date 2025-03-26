from abc import ABC, abstractmethod
import asyncio
import logging
from typing import List, Set

from fraudcrawler.base.settings import MAX_RETRIES, RETRY_DELAY, N_SERP_WKRS, N_ZYTE_WKRS, N_PROC_WKRS
from fraudcrawler import SerpApi, Enricher, ZyteApi

logger = logging.getLogger(__name__)


class Orchestrator(ABC):
    """Abstract base class for orchestrating the different actors (crawling, processing).

    For each pipeline step it will deploy a number of async workers to handle the tasks. In addition
    it makes sure to orchestrate the canceling of the workers only after the relevant workload is done.

    For more information on the orchestrating pattern see README.md.
    """

    def __init__(
        self,
        serpapi_key: str,
        dataforseo_user: str,
        dataforseo_pwd: str,
        zyteapi_key: str,
        openaiapi_key: str,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
        n_serp_wkrs: int = N_SERP_WKRS,
        n_zyte_wkrs: int = N_ZYTE_WKRS,
        n_proc_wkrs: int = N_PROC_WKRS,
    ):
        """Initializes the orchestrator with the given settings.

        Args:
            serpapi_key: The API key for SERP API.
            dataforseo_user: The user for DataForSEO.
            dataforseo_pwd: The password for DataForSEO.
            zyteapi_key: The API key for Zyte API.
            openaiapi_key: The API key for OpenAI.
            max_retries: Maximum number of retries for API calls (optional).
            retry_delay: Delay between retries in seconds (optional).
            n_serp_wkrs: Number of async workers for serp (optional).
            n_zyte_wkrs: Number of async workers for zyte (optional).
            n_proc_wkrs: Number of async workers for the processor (optional).
        """
        # Setup the variables
        self._collected_urls: Set[str] = set()

        # Setup the clients
        self._serpapi = SerpApi(api_key=serpapi_key, max_retries=max_retries, retry_delay=retry_delay)
        self._enricher = Enricher(user=dataforseo_user, pwd=dataforseo_pwd)
        self._zyteapi = ZyteApi(api_key=zyteapi_key, max_retries=max_retries, retry_delay=retry_delay)
        # self._processor = Processor

    @abstractmethod
    async def _collect_results(self, queue_in: asyncio.Queue) -> List | None:
        """Collects the results from the given queue_in.

        Args:
            queue_in: The input queue containing the results.
        """
        pass

    async def _serpapi_execute(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue) -> None:
        """Collects the SerpApi search setups from the queue_in, executes the search and puts the results into queue_out.

        Args:
            queue_in: The input queue containing the search parameters.
            queue_out: The output queue to put the found urls.
        """
        while True:
            item = await queue_in.get()
            if item is None:
                queue_in.task_done()
                break

            try:
                urls = await self._serpapi.search(**item)
                for u in urls:
                    await queue_out.put(u)
            except Exception as e:
                logger.error(f"Error executing SERP API search: {e}")
            queue_in.task_done()
        
    async def _collect_url(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue) -> None:
        """Collects the URLs from the given queue_in, checks for duplicates, and puts them into the queue_out.

        Args:
            queue_in: The input queue containing the URLs.
            queue_out: The output queue to put the URLs.
        """
        while True:
            url = await queue_in.get()
            if url is None:
                queue_in.task_done()
                break

            if url not in self._collected_urls:
                self._collected_urls.add(url)
                await queue_out.put(url)
            queue_in.task_done()

    async def _zyteapi_execute(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue) -> None:
        """.

        Args:
            queue_in: The input queue containing URLs to fetch product details from.
            queue_out: The output queue to put the product details as dictionaries.
        """
        while True:
            url = await queue_in.get()
            if url is None:
                queue_in.task_done()
                break

            try:
                product = await self._zyteapi.get_details(url=url)
                await queue_out.put(product)
            except Exception as e:
                logger.warning(f"Ignoring product from URL {url} due to error: {e}.")
            queue_in.task_done()

# TODO: put None for stopping url_collection also if no enrichment happens


