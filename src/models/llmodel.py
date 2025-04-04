import openai
from openai import OpenAI


class LLModel:

    def __init__(self, model_name: str, api_key: str, endpoint: str, system_prompt: str = None):
        """
        Initialize the LLModel with model name, API key and endpoint.
        :param model_name: Name of the model
        :param api_key: API key for authentication
        :param endpoint: Endpoint for the model
        """
        self.model_name = model_name
        self.api_key = api_key
        self.endpoint = endpoint
        self.system_prompt = system_prompt

        self.client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
        )

    def generate_response(self, prompt: str):
        """
        Generate a response from the model.
        :param prompt: The input prompt for the model
        :param temperature: Sampling temperature
        :param max_tokens: Maximum number of tokens to generate
        :return: Model response
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role":"system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
        )

        print(response)

        return response.choices[0].message.content