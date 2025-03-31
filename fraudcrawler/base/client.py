import asyncio
from datetime import datetime
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List

import pandas as pd

from fraudcrawler.settings import ROOT_DIR
from fraudcrawler.base.base import Setup, Location, Deepness, Host
from fraudcrawler.base.orchestrator import Orchestrator, ProductItem

logger = logging.getLogger(__name__)

_RESULTS_DIR = ROOT_DIR / "data" / "results"

class Results(BaseModel):
    """The results of the product search."""

    search_term: str
    filename: Path | None = None


class FraudCrawlerClient(Orchestrator):
    """The main client for FraudCrawler."""

    _filename_template = "{search_term}_{timestamp}.csv"

    def __init__(self):
        setup = Setup()
        super().__init__(
            serpapi_key=setup.serpapi_key,
            dataforseo_user=setup.dataforseo_user,
            dataforseo_pwd=setup.dataforseo_pwd,
            zyteapi_key=setup.zyteapi_key,
            openaiapi_key=setup.openaiapi_key,
        )

        self._results_dir = _RESULTS_DIR
        if not self._results_dir.exists():
            self._results_dir.mkdir(parents=True)
        self._results: List[Results] = []

    async def _collect_results(self, queue_in):
        """Collects the results from the given queue_in and saves it as csv.

        Args:
            queue_in: The input queue containing the results.
        """
        products = []
        while True:
            product: ProductItem = await queue_in.get()
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
                "is_relevant": product.is_relevant,
            }
            products.append(row)
            queue_in.task_done()

        df = pd.DataFrame(products)
        filename = self._results[-1].filename
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
        timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        filename = self._results_dir / self._filename_template.format(
            search_term=search_term,
            timestamp=timestamp,
        )
        self._results.append(Results(search_term=search_term, filename=filename))

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

    def load_results(self, index: int = -1) -> pd.DataFrame:
        """Loads the results from the saved .csv files.
        
        Args:
            index: The index of the results to load (`incex=-1` are the results for the most recent run).
        """

        results = self._results[index]
        return pd.read_csv(results.filename)
    
    def print_available_results(self) -> None:
        """Prints the available results."""
        n_res = len(self._results)
        for i, res in enumerate(self._results):
            print(f"index={-n_res+i}: {res.search_term} - {res.filename}")
