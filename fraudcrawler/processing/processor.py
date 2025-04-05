import logging

from openai import AsyncOpenAI
from fraudcrawler.settings import USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class Processor:
    """
    Processes product data for classification based on a prompt configuration.
    """

    def __init__(self, api_key: str, model: str):
        """
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
        """
        Calls the OpenAI API with the given user prompt.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI API")
        return content

    async def classify(
        self, prompt: dict, url: str, name: str | None, description: str | None
    ) -> int:
        """
        A generic classification method that:
          1. Pulls system/user prompts from the `prompt` dictionary.
          2. Dynamically substitutes placeholders (e.g., {context}, {url}, {name}, {description}).
          3. Invokes the OpenAI API and returns an integer classification.

        The `prompt` dict is expected to have at least:
          {
             "prompt_name": <identifier string>,
             "system_prompt": <system prompt string>,
             "user_prompt": <user prompt template with placeholders>,
             "allowed_classes": "0,1",  # or some other comma-separated classes
             "default_if_missing": <default fallback int if name or description is None>
          }

        Args:
            prompt: A dictionary with keys "system_prompt", "user_prompt", etc.
            url: Product URL (often used in the user_prompt).
            name: Product name (often used in the user_prompt).
            description: Product description (often used in the user_prompt).

        Returns:
            int: The classification result. Returns -1 if there's an error, or if the response isn't in allowed_classes.
        """

        # If required fields are missing, return the prompt's default fallback if provided.
        if name is None or description is None:
            return prompt.get("default_if_missing", -1)

        system_prompt = prompt["system_prompt"]
        user_prompt_template = USER_PROMPT_TEMPLATE

        # Substitute placeholders in user_prompt with the relevant arguments
        user_prompt = user_prompt_template.format(
            context=prompt["context"] or "",
            url=url or "",
            name=name or "",
            description=description or "",
        )

        # Call the OpenAI API
        try:
            content = await self._call_openai_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1,
            )
            classification_str = content.strip()

            # Enforce that the classification is in the allowed classes
            allowed = prompt.get("allowed_classes")
            if allowed is None or classification_str not in allowed:
                raise ValueError(f"Unexpected classification: {classification_str}")

            classification = int(classification_str)
            logger.info(
                f'Classification for "{name}" (prompt={prompt["prompt_name"]}): {classification}'
            )
            return classification

        except Exception as e:
            logger.error(
                f"Error classifying product '{name}' with prompt '{prompt['prompt_name']}': {e}"
            )
            return -1
