
from typing import Optional
from openai import OpenAI
from openai.types import CompletionUsage

from src.models.model import Model


class LLModel(Model):

    def __init__(self, model_name: str, api_key: str, endpoint: str, system_prompt: str = None):
        """
        Initialize the LLModel with model name, API key and endpoint.
        :param model_name: Name of the model
        :param api_key: API key for authentication
        :param endpoint: Endpoint for the model
        """
        self.model_name : str = model_name
        self.api_key : str = api_key
        self.endpoint : str = endpoint
        self.system_prompt : str = system_prompt

        self.usage : Optional[CompletionUsage] = None

        self.client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
        )

    def generate_response(self, prompt: str, image_urls: Optional[list[str]] = None) -> str:
        """
        Generate a response from the model.
        :param image_urls: List of image URLs to be included in the prompt, the model needs to support vision.
        :param prompt: The input prompt for the model.
        :return: Model response.
        """

        images = []
        if image_urls is not None:
            for url in image_urls:
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                })

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                    {"type": "text", "text": prompt}
                    ] + images  # Merge text + images into one list
                }
            ],
        )

        self.usage = response.usage

        print(self.usage)

        return response.choices[0].message.content

    def get_last_usage(self) -> Optional[CompletionUsage]:
        """
        Get the last usage information.
        :return: Usage information
        """
        return self.usage