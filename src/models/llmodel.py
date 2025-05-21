from typing import Optional, Union, Type
from openai import OpenAI
from openai.types import CompletionUsage
from pydantic import BaseModel


class LLModel:

    def __init__(
        self, model_name: str, api_key: str, endpoint: str, system_prompt: str = None, output_cost: float = 0, input_cost: float = 0
    ):
        """
        Initialize the LLModel with model name, API key and endpoint.
        :param model_name: Name of the model
        :param api_key: API key for authentication
        :param endpoint: Endpoint for the model
        :param system_prompt: System prompt to be used
        :param output_cost: Cost per token for output
        :param input_cost: Cost per token for input
        :return: None
        """
        self.model_name: str = model_name
        self.api_key: str = api_key
        self.endpoint: str = endpoint
        self.system_prompt: str = system_prompt

        self.usage: Optional[CompletionUsage] = None

        self.output_cost: float = output_cost
        self.input_cost: float = input_cost

        self.client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
        )

    def __copy__(self):
        # shallow copy: shares the same client but new usage slot
        cls = self.__class__
        new = cls(self.model_name, self.api_key, self.endpoint, self.system_prompt, self.output_cost, self.input_cost)

        new.client = self.client
        new.usage = None
        return new

    def generate_response(
        self,
        prompt: str,
        image_urls: Optional[list[str]] = None,
        structure: Type[BaseModel] = None,
    ) -> Union[str, BaseModel]:
        """
        Generate a response from the model.
        :param image_urls: List of image URLs to be included in the prompt, the model needs to support vision.
        :param prompt: The input prompt for the model.
        :param structure: Forces the model to respond in specific structure, if provided. Otherwise the model will return string.
        :return: Model response.
        """

        images = []
        if image_urls is not None:
            for url in image_urls:
                images.append({"type": "image_url", "image_url": {"url": url}})

        messages = []

        if self.system_prompt is not None:
            messages.append({"role": "system", "content": self.system_prompt})

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": prompt}] + images,  # Merge text + images
        })

        settings = {
            "model": self.model_name,
            "messages": messages,
        }

        if structure is not None:
            schema = structure.model_json_schema()
            schema["additionalProperties"] = False

            settings["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": structure.__name__,
                    "strict": True,
                    "schema": schema,
                },
            }

        response = self.client.chat.completions.create(
            **settings,
        )

        self.usage = response.usage

        if structure is not None:
            try:
                return structure.model_validate_json(response.choices[0].message.content)
            except:
                print("Failed to validate structure. Your chosen model most likely doesn't support structured output.")
                print(f"Model name: {self.model_name} from {self.endpoint}")
                print(f"Response: {response.choices[0].message.content}")
                raise ValueError(
                    "Failed to validate structure. Your chosen model most likely doesn't support structured output."
                )
        else:
            return response.choices[0].message.content

    def get_last_usage(self) -> Optional[CompletionUsage]:
        """
        Get the last usage information.
        :return: Usage information
        """
        return self.usage

    def get_cost(self) -> float:
        """
        Get the cost of the last usage.
        :return: Cost information
        """
        if self.usage is None:
            return 0

        return (self.usage.prompt_tokens / 1_000_000 ) * self.input_cost + (self.usage.completion_tokens / 1_000_000 ) * self.output_cost

