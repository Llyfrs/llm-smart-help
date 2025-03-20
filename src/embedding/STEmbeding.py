from typing import Dict, Any

from src.embedding.EmbeddingModel import EmbeddingModel
from sentence_transformers import SentenceTransformer


class STEmbedding(EmbeddingModel):
    """
    Wrapper class for the SentenceTransformer library.
    """

    def __init__(self, model_name, *args, **kwargs):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device="cuda", *args, **kwargs)
        super().__init__()

    def embed(self, data):
        return self.model.encode(data, normalize_embeddings=True)

    def tokenize(self, data):
        return self.model.tokenize(data)

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
