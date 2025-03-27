from datetime import datetime
import logging

import pandas as pd

from fraudcrawler.base.settings import ROOT_DIR
from fraudcrawler.base.base import Setup
from fraudcrawler import Orchestrator

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

        self._data_dir = ROOT_DIR / "data"
        if not self._data_dir.exists():
            self._data_dir.mkdir()
        
    async def _collect_results(self, queue_in):
        """Collects the results from the given queue_in and saves it as csv.

        Args:
            queue_in: The input queue containing the results.
        """
        products = []
        while True:
            result = await queue_in.get()
            if result is None:
                queue_in.task_done()
                break
            
            row = {
                "search_term": result.search_term,
                "search_term_type": result.search_term_type,
                "url": result.url,
                "product_name": result.product_name,
                "product_price": result.product_price,
                "product_description": result.product_description,
                "prokduct_probability": result.product_probability,
            }
            products.append(row)
            queue_in.task_done()
        
        df = pd.DataFrame(products)
        today = datetime.today().strftime('%Y%m%d')
        filename = f"products_{today}_{result.search_term}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Results saved to {filename}")
