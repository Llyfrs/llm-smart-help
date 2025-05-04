from typing import Dict, Any, List

from src.models.embedding_model import EmbeddingModel
from sentence_transformers import SentenceTransformer


class STEmbedding(EmbeddingModel):
    """
    Wrapper class for the SentenceTransformer library.
    """

    def __init__(self, model_name, prompt:str = None, *args, **kwargs):
        super().__init__(prompt=prompt)

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, *args, **kwargs)

    def max_tokens(self) -> int:
        return self.model.tokenizer.model_max_length



    def __copy__(self):
        # Create new wrapper without re-running __init__
        cls = self.__class__
        new = cls.__new__(cls)
        # Copy base attributes
        EmbeddingModel.__init__(new, prompt=self.prompt)
        # Share the same SentenceTransformer instance
        new.model_name = self.model_name
        new.model = self.model
        return new

    def embed(self, data, instruction=None):

        if instruction:
            data = [self.apply_prompt(instruction, d) for d in data]

        return self.model.encode(data, normalize_embeddings=True)

    def tokenize(self, data: str) -> List[int]:
        return self.model.tokenizer.encode(data, add_special_tokens=True)


    def get_dimension(self):
        return self.model.get_sentence_embedding_dimension()

    def metadata(self) -> Dict[str, Any]:
        return {
            # Current fields
            "model": self.model.__class__.__name__,
            "model_name": self.model.__class__.__name__,  # Consider using self.model.name instead
            "model_version": self.model._version,
            "model_device": self.model.device,
            "model_max_seq_length": self.model.max_seq_length,
            # Additional useful fields
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "tokenizer_name": self.model.tokenizer.__class__.__name__,
            "tokenizer_vocab_size": (
                len(self.model.tokenizer.vocab)
                if hasattr(self.model.tokenizer, "vocab")
                else None
            ),
            "pooling_strategy": (
                self.model.pooling_model.__class__.__name__
                if hasattr(self.model, "pooling_model")
                else None
            ),
            "normalize_embeddings": True,  # Since you're setting this in embed()
            "model_base_name": self.model_name,  # The name passed during initialization
            "model_architecture": (
                self.model.auto_model.__class__.__name__
                if hasattr(self.model, "auto_model")
                else None
            ),
            "supports_tokenization": hasattr(self.model, "tokenize"),
        }
