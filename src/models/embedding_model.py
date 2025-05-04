from typing import List
import numpy as np
from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    """
    Abstract base class for all embedding models.
    """
    def __init__(self, prompt: str = None):
        """
        Initialize the embedding model.
        :param prompt: Prompt to be used for the embedding model.
        """
        self.model_name = None
        self.prompt = prompt

    def apply_prompt(self, instruction: str, query: str) -> str:
        """
        Apply the prompt to the data.
        :param instruction: The instruction to be included in the prompt.
        :param query: The query to be included in the prompt.
        :return: The formatted prompt.
        """
        final_prompt = query
        if self.prompt:

            final_prompt = self.prompt

            if "{query}" in self.prompt:
                final_prompt = final_prompt.replace("{query}", query)
            else:
                raise ValueError("Prompt must contain {query} placeholder.")

            if "{instruction}" in self.prompt:
                final_prompt = final_prompt.replace("{instruction}", instruction)

        return final_prompt

    @abstractmethod
    def embed(self, data: List[str], instruction :str =None) -> List[np.array]:
        """Embed a list of strings into a list of vectors."""
        pass

    @abstractmethod
    def tokenize(self, data: str) -> List[int]:
        """Tokenize a list of strings into a list of tokens."""
        pass

    @abstractmethod
    def metadata(self) -> str:
        """Return metadata about the embedding model."""
        pass


    @abstractmethod
    def get_dimension(self) -> int:
        """Return the dimension of the embedding."""
        pass

    @abstractmethod
    def max_tokens(self) -> int:
        """
        Return the maximum number of tokens for the model.
        :return: Maximum number of tokens.
        """
        return 0
