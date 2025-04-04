from dataclasses import dataclass
from typing import List, Optional


from dataclasses import dataclass
from typing import List, Optional

from src.preprocesing.chunk import Chunk


@dataclass
class Vector:
    """
    A class to represent a vector in a vector storage.
    """
    vector: List[float]
    file_name: str
    file_position: int
    content: str
    metadata: dict
    id: Optional[int] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_chunk(cls, chunk: Chunk, vector: List[float]) -> "Vector":
        """
        Create a new Vector instance from a Chunk instance.
        :param chunk: The Chunk instance to initialize from.
        :param vector: The vector to be associated with this chunk.
        :return: A new Vector instance.
        """
        return cls(
            vector=vector,
            file_name=chunk.file_name,
            file_position=chunk.file_position,
            content=chunk.content,
            metadata=chunk.metadata,
            id=None,
            updated_at=None
        )

