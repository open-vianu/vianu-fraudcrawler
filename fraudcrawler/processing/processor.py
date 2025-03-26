import asyncio
import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI

from fraudcrawler.base.settings import ZYTE_PROBABILITY_THRESHOLD

logger = logging.getLogger(__name__)


class Processor:
    """Processes the product data and applies specific filtering rules."""

    _system_prompt = (
        "You are a helpful and intelligent assistant. Your task is to classify any given product "
        "as either relevant (1) or not relevant (0), strictly based on the context and product details provided by the user. "
        "You must consider all aspects of the given context and make a binary decision accordingly. "
        "If the product aligns with the user's needs, classify it as 1 (relevant); otherwise, classify it as 0 (not relevant). "
        "Respond only with the number 1 or 0."
    )

    _user_prompt_template = "Context: {context}\n\nProduct Details: {name}\n{description}\n\nRelevance:"

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initializes the Processor with the given location.

        Args:
            location: The location used to process the products.
            context: The context associated to the field of interest.
            api_key: The OpenAI API key.
            model: The OpenAI model to use (default: "gpt-4o").
        """
        country_code = self._location_mapping[location].lower()
        if country_code is None:
            logger.warning(
                f'Location {location} not found in self._location_mapping (defaulting to "ch").'
            )
            country_code = "ch"
        self._country_code = country_code.lower()
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._context = context

    def _keep_product_country_code(self, product: dict) -> bool:
        """Determines whether to keep the product based on the country_code.

        Args:
            product: A product data dictionary.
        """
        url = product.get("url", "")
        return (
            f".{self._country_code}/" in url.lower()
            or url.lower().endswith(f".{self._country_code}")
            or ".com" in url.lower()
        )
    
    def _keep_product_zyte_probability(self, product: dict) -> bool:
        """Determines whether to keep the product based on the Zyte probability threshold.

        Args:
            product: A product data dictionary.
        """
        try:
            prob = product['product']['metadata']['probability']
        except KeyError:
            logger.warning(f"Product with url={product.get('url')} has no zyte probability value - product is ignored")
            return False

        return prob > ZYTE_PROBABILITY_THRESHOLD


    def _keep_product(self, product: dict) -> bool:
        """Determines whether to keep the product or filter it out.

        Args:
            product: A product data dictionary.
        """
        if not self._keep_product_country_code(product):
            logger.debug(f"Product URL {product.get('url', '')} does not match country code.")
            return False
        elif not self._keep_product_zyte_probability(product):
            logger.debug(f"Product URL {product.get('url', '')} does not meet Zyte probability threshold.")
            return False
        
        return True

    @staticmethod
    def _handle_missing_fields(product: Dict[str, Any], field: str) -> Dict[str, Any]:
        if field not in product["product"]:
            product["product"][field] = (
                "MISSING DATA, VIANU MODIFIED - it is a relevant product"
            )
            logger.warning(f"Product data in field '{field}' does not exist.")
        return product

    async def _is_relevant(self, product: Dict[str, Any]) -> int:
        """Classifies a single product as suspicious (1) or not suspicious (0) based on the given context.

        Args:
            product: The product json contents including URL, PRODUCT_NAME, PRODUCT_DESCRIPTION.
        """

        # Set up user prompt
        product = self._handle_missing_fields(product, "name")
        product = self._handle_missing_fields(product, "description")
        user_prompt = self._user_prompt_template.format(
            context=self._context,
            name=product["product"]["name"],
            description=product["product"]["description"],
        )

        # Query OpenAI API
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1,  # Ensuring a short response
            )

            classification = response.choices[0].message.content.strip()
            if classification not in ["0", "1"]:
                raise ValueError(
                    f"Unexpected response from OpenAI API: {classification}"
                )

            logger.info(
                f"CLASSIFIED PRODUCT -- {product['product']['name']} -- as {classification}"
            )
            return int(classification)

        except Exception as e:
            logger.error(f"Error classifying product: {e}")
            return -1  # Indicate an error occurred

    async def _classify_product(self, product):
        product["is_relevant"] = await self._is_relevant(product)
        return product

    async def apply(
        self, queue_in: asyncio.Queue, queue_out: asyncio.Queue
    ) -> List[dict]:
        """Processes the product data and filters based on country_code and classifies the products.

        Args:
            products: A list of product data dictionaries.
        """

        while True:
            item = await queue_in.get()
            if item is None:
                queue_in.task_done()
                break
            if self._keep_product(item):
                item = await self._classify_product(item)
                await queue_out.put(item=item)
            else:
                logger.warning(
                    f"Ignoring product from URL {item.get('url', '')} by filter criteria."
                )

            queue_in.task_done()
