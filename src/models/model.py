from abc import abstractmethod, ABC
from typing import Optional

from openai.types import CompletionUsage


class Model(ABC):

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the model.
        :param prompt: The input prompt for the model
        :return: Model response
        """
        pass

    @abstractmethod
    def get_last_usage(self) -> Optional[CompletionUsage]:
        """
        Get the last usage information.
        :return: Usage information
        """

        pass