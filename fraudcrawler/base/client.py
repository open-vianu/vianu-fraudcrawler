import asyncio
from datetime import datetime
import logging
from typing import List

import pandas as pd

from fraudcrawler.settings import ROOT_DIR
from fraudcrawler.base.base import Setup, Location, Deepness, Host
from fraudcrawler.base.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class FraudCrawlerClient(Orchestrator):
    """The main client for FraudCrawler."""


    def __init__(self):
        setup = Setup()
        super().__init__(
            serpapi_key=setup.serpapi_key,
            dataforseo_user=setup.dataforseo_user,
            dataforseo_pwd=setup.dataforseo_pwd,
            zyteapi_key=setup.zyteapi_key,
            openaiapi_key=setup.openaiapi_key,
        )

        self._data_dir = ROOT_DIR / "data" / "products"
        if not self._data_dir.exists():
            self._data_dir.mkdir(parents=True)
        
    async def _collect_results(self, queue_in):
        """Collects the results from the given queue_in and saves it as csv.

        Args:
            queue_in: The input queue containing the results.
        """
        products = []
        while True:
            product = await queue_in.get()
            if product is None:
                queue_in.task_done()
                break
            
            row = {
                "search_term": product.search_term,
                "search_term_type": product.search_term_type,
                "url": product.url,
                "marketplace_name": product.marketplace_name,
                "product_name": product.product_name,
                "product_price": product.product_price,
                "product_description": product.product_description,
                "probability": product.probability,
            }
            products.append(row)
            queue_in.task_done()
        
        df = pd.DataFrame(products)
        today = datetime.today().strftime('%Y%m%d%H%M%S')
        filename = self._data_dir / f'{today}.csv'
        df.to_csv(filename, index=False)
        logger.info(f"Results saved to {filename}")

    def run(
        self,
        search_term: str,
        location: Location,
        deepness: Deepness,
        context: str,
        marketplaces: List[Host] | None = None,
        excluded_urls: List[Host] | None = None,
    ) -> None:
        """Runs the pipeline steps: serp, enrich, zyte, process, and collect the results.
        
        Args:
            search_term: The search term for the query.
            location: The location to use for the query.
            deepness: The search depth and enrichment details.
            context: The context prompt to use for detecting relevant products.
            marketplaces: The marketplaces to include in the search.
            excluded_urls: The URLs to exclude from the search.
        """
        asyncio.run(
            super().run(
                search_term=search_term,
                location=location,
                deepness=deepness,
                context=context,
                marketplaces=marketplaces,
                excluded_urls=excluded_urls,
            )
        )
