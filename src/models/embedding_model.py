from typing import List
import numpy as np
from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    """
    Abstract base class for all embedding models.
    """

    @abstractmethod
    def embed(self, data: List[str]) -> List[np.array]:
        """Embed a list of strings into a list of vectors."""
        pass

    @abstractmethod
    def tokenize(self, data: List[str]) -> List[List[str]]:
        """Tokenize a list of strings into a list of tokens."""
        pass

    @abstractmethod
    def metadata(self) -> str:
        """Return metadata about the embedding model."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embedding."""
        pass
