from dataclasses import dataclass


@dataclass
class Paragraph:
    content: str

    def __str__(self) -> str:
        return self.content + "\n\n"
