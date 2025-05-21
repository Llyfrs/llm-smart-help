from dataclasses import dataclass


@dataclass
class Paragraph:

    """
    Paragraph is a simple class that represents a paragraph in markdown format.
    """

    content: str

    def __str__(self) -> str:
        return self.content + "\n\n"
