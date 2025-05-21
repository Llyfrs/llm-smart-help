from dataclasses import dataclass


@dataclass
class Image:

    """
    Image is a simple class that represents an image in markdown format, using the syntax ![alt text](url).
    """

    url: str
    alt: str

    def __str__(self) -> str:
        return f"![{self.alt}]({self.url})"

    def parse(self, root):
        pass
