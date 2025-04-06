from typing import Union, List

import numpy as np
import tiktoken

from src.models.embedding_model import EmbeddingModel
from openai import OpenAI

class OAEmbedding(EmbeddingModel):

    """
    This class is a wrapper for the OpenAI API to generate embeddings.
    """

    def __init__(self, model_name: str, api_key: str, dimension: int, endpoint: str = "https://api.openai.com/v1", *args, **kwargs):
        """
        Initialize the OAEmbedding model.
        :param model_name: Name of the embedding model.
        """
        self.model_name = model_name
        self.l_dimension = dimension

        self.client = OpenAI(
            base_url=endpoint,
            api_key=api_key,
            *args,
            **kwargs
        )


    def embed(self, data: List[str]) -> List[np.array]:
        """

        Embed a list of strings into a list of vectors.
        :param data:
        :return:
        """

        response = self.client.embeddings.create(
            model=self.model_name,
            input=data
        )

        return [np.array(d.embedding) for d in response.data]


    def tokenize(self, data: str) -> list[int]:
        """
        Tokenize a list of strings into a list of tokens.
        :param data:
        :return:
        """
        encoding = None
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens = encoding.encode(data)
        return tokens

    def metadata(self) -> str:
        """
        Return metadata about the embedding model.
        :return:
        """
        return {}

    @property
    def dimension(self) -> int:
        """
        Return the dimension of the embedding.
        :return:
        """
        return self.l_dimension