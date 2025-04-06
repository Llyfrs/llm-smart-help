from dataclasses import field, dataclass
from typing import Dict, List

from .section import Section


@dataclass
class Document:
    file_name: str
    metadata: Dict[str, str] = field(default_factory=dict)
    sections: List[Section] = field(default_factory=list)

    def __str__(self) -> str:
        document = ""

        if self.metadata:
            document += "---\n"
            for key, value in self.metadata.items():
                document += f"{key}: {value}\n"

            document += "---\n\n"

        for section in self.sections:
            document += str(section) + "\n\n"

        return document

    def get_tree_str(self) -> str:
        def _build_tree(sections, indent=0):
            tree = ""
            for sec in sections:
                if isinstance(sec, Section):
                    tree += " " * indent + f"{sec.title} (h{sec.level})\n"
                    tree += _build_tree(sec.content, indent + 2)
            return tree

        return _build_tree(self.sections)

    def print_tree(self):
        print(self.get_tree_str())
