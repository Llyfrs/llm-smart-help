from dataclasses import dataclass
from typing import List


@dataclass
class BulletList:
    """
    BulletList is a simple class that represents a list of items in a bullet format.
    """
    items: List[str]

    def __str__(self) -> str:
        bullet_list = ""
        for item in self.items:
            bullet_list += f"- {item}\n"

        return bullet_list
