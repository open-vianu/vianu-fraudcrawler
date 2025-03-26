from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Dict, List, Set

from fraudcrawler.base.settings import PROCESSOR_MODEL, MAX_RETRIES, RETRY_DELAY, N_SERP_WKRS, N_ZYTE_WKRS, N_PROC_WKRS
from fraudcrawler.base.base import Deepness, Host, Language, Location
from fraudcrawler import SerpApi, Enricher, ZyteApi, Processor

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
        openai_model: str = PROCESSOR_MODEL,
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
            openai_model: The model to use for the processing (optional).
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
        self._processor = Processor(api_key=openaiapi_key, model=openai_model)

        # Setup the async framework
        self._n_serp_wkrs = n_serp_wkrs
        self._n_zyte_wkrs = n_zyte_wkrs
        self._n_proc_wkrs = n_proc_wkrs
        self._queues: Dict[str, asyncio.Queue] | None = None 
        self._workers: Dict[str, List[asyncio.Task] | asyncio.Task] | None = None

    async def _serp_execute(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue) -> None:
        """Collects the SerpApi search setups from the queue_in, executes the search, filters the results (country_code) and puts them into queue_out.

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
                urls = await self._serpapi.apply(**item)
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

    async def _zyte_execute(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue, threshold: float) -> None:
        """Collects the URLs from the queue_in, enriches it with product details metadata, filters them (probability), and puts them into queue_out.

        Args:
            queue_in: The input queue containing URLs to fetch product details from.
            queue_out: The output queue to put the product details as dictionaries.
            threshold: The probability threshold used to filter the products.
        """
        while True:
            url = await queue_in.get()
            if url is None:
                queue_in.task_done()
                break

            try:
                product = await self._zyteapi.apply(url=url)
                if self._zyteapi.keep_product(product=product, threshold=threshold):
                    await queue_out.put(product)
                else:
                    logger.debug(f'Product with url="{url}" does not meet probability threshold.')
            except Exception as e:
                logger.warning(f"Error executing Zyte API search: {e}.")
            queue_in.task_done()

    async def _proc_execute(self, queue_in: asyncio.Queue, queue_out: asyncio.Queue, context: str) -> None:
        """Collects the product details from the queue_in, processes them (filtering, relevance, etc.) and puts the results into queue_out.
        
        Args:
            queue_in: The input queue containing the product details.
            queue_out: The output queue to put the processed product details.
            context: The context to use for the processing.
        """

        # Process the products
        while True:
            product = await queue_in.get()
            if product is None:
                queue_in.task_done()
                break

            try:
                product = await self._processor.classify_product(product=product, context=context)
                await queue_out.put(product)
            except Exception as e:
                logger.warning(f"Error processing product: {e}.")
            queue_in.task_done()


    @abstractmethod
    async def _collect_results(self, queue_in: asyncio.Queue) -> None:
        """Collects the results from the given queue_in.

        Args:
            queue_in: The input queue containing the results.
        """
        pass


    def _setup_async_framework(
            self,
            n_serp_wkrs: int,
            n_zyte_wkrs: int,
            n_proc_wkrs: int,
            country_code: str,
            threshold: float,
            context: str,
        ) -> List[asyncio.Queue]:
        """Sets up the necessary queues and workers for the async framework.

        Args:
            n_serp_wkrs: Number of async workers for serp.
            n_zyte_wkrs: Number of async workers for zyte.
            n_proc_wkrs: Number of async workers for processor.
            country_code: The country code used to filter the products (func:`Processor.keep_product`).
            threshold: The probability threshold used to filter the products (func:`Processor.keep_product`).
            context: The context used by the LLM for determining if a product is suspicious (func:`Processor.classify_product`).

        """

        # Setup the input/output queues for the workers
        serp_queue = asyncio.Queue()
        url_queue = asyncio.Queue()
        zyte_queue = asyncio.Queue()
        proc_queue = asyncio.Queue()
        res_queue = asyncio.Queue()

        # Setup the Serp workers
        serp_wkrs = [
            asyncio.create_task(
                self._serp_execute(
                    queue_in=serp_queue,
                    queue_out=url_queue,
                )
            )
            for _ in range(n_serp_wkrs)
        ]

        # Setup the URL collector
        url_col = asyncio.create_task(self._collect_url(queue_in=url_queue, queue_out=zyte_queue))

        # Setup the Zyte workers
        zyte_wkrs = [
            asyncio.create_task(
                self._zyte_execute(
                    queue_in=zyte_queue,
                    queue_out=proc_queue,
                )
            )
            for _ in range(n_zyte_wkrs)
        ]

        # Setup the processing workers
        proc_wkrs = [
            asyncio.create_task(
                self._proc_execute(
                    queue_in=proc_queue,
                    queue_out=res_queue,
                    country_code=country_code,
                    threshold=threshold,
                    context=context,
                )
            )
            for _ in range(n_proc_wkrs)
        ]

        # Setup the result collector
        res_col = asyncio.create_task(self._collect_results(queue_in=res_queue))

        # Add the setup to the instance variables
        self._queues: Dict[str, asyncio.Queue] = {
            "serp": serp_queue,
            "url": url_queue,
            "zyte": zyte_queue,
            "proc": proc_queue,
            "res": res_queue,
        }
        self._workers: Dict[str, List[asyncio.Task] | asyncio.Task] = {
            "serp": serp_wkrs,
            "url": url_col,
            "zyte": zyte_wkrs,
            "proc": proc_wkrs,
            "res": res_col,
        }

    async def run(
        self,
        search_term: str,
        language: Language,
        location: Location,
        deepness: Deepness,
        marketplaces: List[Host] | None,
        excluded_urls: List[Host] | None,
        threshold: float,
        context: str,
    ) -> None:
        """Runs the pipeline steps: serp, enrich, zyte, process, and collect the results.
        
        Args:
            search_term: The search term for the query.
            language: The language to use for the query.
            location: The location to use for the query.
            deepness: The search depth and enrichment details.
            marketplaces: The marketplaces to include in the search.
            excluded_urls: The URLs to exclude from the search.
        """
        # Setup the async framework
        n_terms_max = 1 + deepness.enrichment.additional_terms if deepness.enrichment else 0
        n_serp_wkrs = min(self._n_serp_wkrs, n_terms_max)
        n_zyte_wkrs = min(self._n_zyte_wkrs, deepness.num_results)
        n_proc_wkrs = min(self._n_proc_wkrs, deepness.num_results)
        logger.debug(
            f"setting up async framework (#workers: serp={n_serp_wkrs}, zyte={n_zyte_wkrs}, proc={n_proc_wkrs})"
        )
        self._setup_async_framework(
            n_serp_wkrs=n_serp_wkrs,
            n_zyte_wkrs=n_zyte_wkrs,
            n_proc_wkrs=n_proc_wkrs,
            country_code=location.code,
            threshold=threshold,
            context=language.code,
        )




# TODO: put None for stopping url_collection also if no enrichment happens


