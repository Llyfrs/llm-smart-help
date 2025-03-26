from dataclasses import dataclass
from typing import List


@dataclass
class Vector:
    """
    A class to represent a vector in a vector storage.
    """
    id : int
    vector: List[float]
    file_name: str
    file_position: int
    content: str
    metadata: dict
    updated_at: int

