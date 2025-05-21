from dataclasses import dataclass


@dataclass
class Chunk:
    """
    A class to represent a chunk of text.
    """
    content: str
    file_name: str
    file_position: int
    metadata: dict

    def __str__(self) -> str:
        return self.content
