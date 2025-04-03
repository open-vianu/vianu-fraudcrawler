import logging

from openai import AsyncOpenAI

from fraudcrawler.settings import PROCESSOR_MISSING_FIELDS_DEFAULT_RELEVANCE


logger = logging.getLogger(__name__)


class Processor:
    """Processes the product data for assessing its relevance."""

    _system_prompt = (
        "You are a helpful and intelligent assistant. Your task is to classify any given product "
        "as either relevant (1) or not relevant (0), strictly based on the context and product details provided by the user. "
        "You must consider all aspects of the given context and make a binary decision accordingly. "
        "If the product aligns with the user's needs, classify it as 1 (relevant); otherwise, classify it as 0 (not relevant). "
        "Respond only with the number 1 or 0."
    )

    _user_prompt_template = (
        "Context: {context}\n\nProduct Details: {name}\n{description}\n\nRelevance:"
    )

    def __init__(self, api_key: str, model: str):
        """Initializes the Processor with the given location.

        Args:
            api_key: The OpenAI API key.
            model: The OpenAI model to use.
        """
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _is_relevant(self, context: str, name: str, description: str) -> int:
        """Classifies a single product as suspicious (1) or not suspicious (0) based on the given context.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            name: The name of the product.
            description: The description of the product.
        """

        # Set up user prompt
        user_prompt = self._user_prompt_template.format(
            context=context,
            name=name,
            description=description,
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

            # Extract and validate the response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI API")
            classification = content.strip()
            if classification not in ["0", "1"]:
                raise ValueError(
                    f"Unexpected response from OpenAI API: {classification}"
                )

            logger.info(f'classified product "{name}" as {classification}')
            return int(classification)

        except Exception as e:
            logger.error(f"Error classifying product: {e}")
            return -1  # Indicate an error occurred

    async def classify_product(
        self, context: str, name: str | None, description: str | None
    ) -> int:
        """Adds a field 'is_relevant' to the product based on the classification.

        Args:
            context: The context used by the LLM for determining if a product is suspicious.
            name: The name of the product.
            description: The description of the product.
        """

        # If name or description is missing, return default relevance
        if name is None or description is None:
            return PROCESSOR_MISSING_FIELDS_DEFAULT_RELEVANCE
        
        # Otherwise, classify the product based on the given context
        return await self._is_relevant(
            context=context, name=name, description=description
        )
