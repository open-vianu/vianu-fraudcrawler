import logging

from openai import AsyncOpenAI

from fraudcrawler.settings import PROCESSOR_DEFAULT_MISSING_FIELDS_RELEVANCE, PROCESSOR_DEFAULT_MISSING_FIELDS_PRODUCT


logger = logging.getLogger(__name__)


class Processor:
    """Processes the product data for assessing its relevance."""

    _relevance_system_prompt = (
        "You are a helpful and intelligent assistant. Your task is to classify any given product "
        "as either relevant (1) or not relevant (0), strictly based on the context and product details provided by the user. "
        "You must consider all aspects of the given context and make a binary decision accordingly. "
        "If the product aligns with the user's needs, classify it as 1 (relevant); otherwise, classify it as 0 (not relevant). "
        "Respond only with the number 1 or 0."
    )
    _relevance_user_prompt_template = (
        "Context: {context}\n\nProduct Details: {name}\n{description}\n\nRelevance:"
    )

    _product_system_prompt = (
        "You are a helpful and intelligent assistant. Your task is to classify any given product "
        "as either a product (1) or not a product (0), strictly based on the context and product details provided by the user. "
        "You must consider all aspects of the given context and make a binary decision accordingly. "
        "If the product aligns with the user's needs, classify it as 1 (product); otherwise, classify it as 0 (not a product). "
        "Respond only with the number 1 or 0."
    )
    _product_user_prompt_template = (
        "Context: {context}\n\nProduct Details: {url}\n{name}\n{description}\n\nProduct:"
    )

    def __init__(self, api_key: str, model: str):
        """Initializes the Processor with the given location.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use.
        """
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
    
    async def _call_openai_api(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs,
    ) -> str:
        """Calls the OpenAI API with the given user prompt.

        Args:
            system_prompt: The system prompt to send to the OpenAI API.
            user_prompt: The user prompt to send to the OpenAI API.
        """
        response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs
            )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI API")
        return content


    async def _is_relevant(self, context: str, name: str, description: str) -> int:
        """Classifies a single product as suspicious (1) or not suspicious (0) based on the given context.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            name: The name of the product.
            description: The description of the product.
        """

        # Set up user prompt
        user_prompt = self._relevance_user_prompt_template.format(
            context=context,
            name=name,
            description=description,
        )

        # Query OpenAI API
        try:
            content = await self._call_openai_api(
                system_prompt=self._relevance_system_prompt,
                user_prompt=user_prompt,
                max_tokens=1,
            )
            classification = content.strip()
            if classification not in ["0", "1"]:
                raise ValueError(
                    f"Unexpected response from OpenAI API (relevance classification {classification})"
                )

            logger.info(f'classified product "{name}" as {classification}')
            return int(classification)

        except Exception as e:
            logger.error(f"Error classifying product: {e}")
            return -1  # Indicate an error occurred

    async def is_relevant(
        self, context: str, name: str | None, description: str | None
    ) -> int:
        """Based on the context, name, and description this function assesses the relevance of a product.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            name: The name of the product.
            description: The description of the product.
        """

        # If name or description is missing, return default relevance
        if name is None or description is None:
            return PROCESSOR_DEFAULT_MISSING_FIELDS_RELEVANCE
        
        # Otherwise, classify the product based on the given context
        return await self._is_relevant(
            context=context, name=name, description=description
        )

    async def _is_product(
        self, context: str, url: str, name: str, description: str
    ) -> int:
        """Classifies a single product as a product (1) or not a product (0) based on the given context.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            url: The URL of the product.
            name: The name of the product.
            description: The description of the product.
        """

        # Set up user prompt
        user_prompt = self._product_user_prompt_template.format(
            context=context,
            url=url,
            name=name,
            description=description,
        )

        # Query OpenAI API
        try:
            content = await self._call_openai_api(
                system_prompt=self._product_system_prompt,
                user_prompt=user_prompt,
                max_tokens=1,
            )
            classification = content.strip()
            if classification not in ["0", "1"]:
                raise ValueError(
                    f"Unexpected response from OpenAI API (product classification {classification})"
                )

            logger.info(f'classified product "{name}" as {classification}')
            return int(classification)

        except Exception as e:
            logger.error(f"Error classifying product: {e}")
            return -1


    async def is_product(
        self,
        context: str,
        url: str,
        name: str | None,
        description: str | None
    ) -> int:
        """Based on the context, url, name, and description this function assesses if a product is relevant.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            url: The URL of the product.
            name: The name of the product.
            description: The description of the product.
        """

        # If name or description is missing, return default relevance
        if name is None or description is None:
            return PROCESSOR_DEFAULT_MISSING_FIELDS_PRODUCT
        
        # Otherwise, classify the product based on the given context
        return await self._is_product(
            context=context, url=url, name=name, description=description
        )