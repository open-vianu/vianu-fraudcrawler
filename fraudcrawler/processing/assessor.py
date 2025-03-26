import asyncio
import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class Assessor:
    """Processes the product data for assessing its relevance."""

    _system_prompt = (
        "You are a helpful and intelligent assistant. Your task is to classify any given product "
        "as either relevant (1) or not relevant (0), strictly based on the context and product details provided by the user. "
        "You must consider all aspects of the given context and make a binary decision accordingly. "
        "If the product aligns with the user's needs, classify it as 1 (relevant); otherwise, classify it as 0 (not relevant). "
        "Respond only with the number 1 or 0."
    )

    _user_prompt_template = "Context: {context}\n\nProduct Details: {name}\n{description}\n\nRelevance:"
    _missing_field_message = "MISSING DATA, VIANU MODIFIED - it is a relevant product"

    def __init__(self, api_key: str, model: str):
        """Initializes the Processor with the given location.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use.
        """
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @staticmethod
    def _keep_product_country_code(product: dict, country_code: str) -> bool:
        """Determines whether to keep the product based on the country_code.

        Args:
            product: A product data dictionary.
            country_code: The country code used to filter the products.
        """
        url = product.get("url", "")
        return (
            f".{country_code}/" in url.lower()
            or url.lower().endswith(f".{country_code}")
            or ".com" in url.lower()
        )
    
    def _keep_product_probability(self, product: dict, threshold: str) -> bool:
        """Determines whether to keep the product based on the probability threshold.

        Args:
            product: A product data dictionary.
            threshold: The Zyte probability threshold used to filter the products.
        """
        try:
            prob = product['product']['metadata']['probability']
        except KeyError:
            logger.warning(f"Product with url={product.get('url')} has no probability value - product is ignored")
            return False
        return prob > threshold

    def keep_product(self, product: dict, country_code: str, threshold: float) -> bool:
        """Determines whether to keep the product or filter it out.

        This method applies two different filters:
            - The product URL must match the country code.
            - The Zyte probability must be above the threshold

        Args:
            product: A product data dictionary.
            country_code: The country code used to filter the products.
            threshold: The probability threshold used to filter the products.
        """
        url = product['url']
        if not self._keep_product_country_code(product=product, country_code=country_code):
            logger.debug(f'Product with url="{url}" does not match country_code.')
            return False
        elif not self._keep_product_probability(product=product, threshold=threshold):
            logger.debug(f'Product with url="{url}" does not meet probability threshold.')
            return False
        return True

    def _handle_missing_fields(self, product: Dict[str, Any], field: str) -> Dict[str, Any]:
        if field not in product["product"]:
            product["product"][field] = self._missing_field_message
            logger.warning(f'Product data in field="{field}" did not exist and was handled by processor.')
        return product

    async def _is_relevant(self, product: Dict[str, Any], context: str) -> int:
        """Classifies a single product as suspicious (1) or not suspicious (0) based on the given context.

        Args:
            product: The product data dictionary.
            context: The context used by the LLM for determining if a product is suspicious.
        """

        # TODO: Handle missing fields -> is that what we want ??!!
        product = self._handle_missing_fields(product, "name")
        product = self._handle_missing_fields(product, "description")

        # Set up user prompt
        user_prompt = self._user_prompt_template.format(
            context=context,
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

            logger.info(f'classified product "{product["product"]["name"]}" as {classification}')
            return int(classification)

        except Exception as e:
            logger.error(f"Error classifying product: {e}")
            return -1  # Indicate an error occurred

    async def classify_product(self, product: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Adds a field 'is_relevant' to the product based on the classification.

        Args:
            product: The product data dictionary.
            context: The context used by the LLM for determining if a product is suspicious.
        """
        product["is_relevant"] = await self._is_relevant(product=product, context=context)
        return product
