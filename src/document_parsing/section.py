from dataclasses import dataclass, field
from typing import List, Union

from .bullet_list import BulletList

from .image import Image
from .paragraph import Paragraph
from .table import Table


@dataclass
class Section:
    title: str
    level: int
    content: List[Union[Paragraph, Table, "Section", Image, BulletList]] = field(
        default_factory=list
    )

    def __str__(self) -> str:
        section = "#" * self.level + f" {self.title}\n\n"
        for content in self.content:
            section += str(content)
        return section  # Ensure the section string is returned
