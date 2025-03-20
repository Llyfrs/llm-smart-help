from dataclasses import dataclass


@dataclass
class Image:
    url: str
    alt: str

    def __str__(self) -> str:
        return f"![{self.alt}]({self.url})"

    def parse(self, root):
        pass
