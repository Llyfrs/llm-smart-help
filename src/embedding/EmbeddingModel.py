from typing import List
import numpy as np


class EmbeddingModel:
    """
    Super class for all embedding models.
    """

    def embed(self, data: List[str]) -> List[np.array]:
        raise NotImplementedError("EmbeddingModel::embed method is not implemented")

    def tokenize(self, data: List[str]) -> List[List[str]]:
        raise NotImplementedError("EmbeddingModel::tokenize method is not implemented")

    def metadata(self) -> str:
        raise NotImplementedError("EmbeddingModel::metadata method is not implemented")
