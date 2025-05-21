from dataclasses import field, dataclass
from typing import Dict, List, Optional

from black import datetime

from .section import Section

@dataclass
class Document:
    """
    A class to represent a markdown document. Contains tree-like structure of sections, paragraphs, tables, images, and bullet lists.
    To load existing document use class DocumentParser.
    """

    file_name: str
    metadata: Dict[str, str] = field(default_factory=dict)
    sections: List[Section] = field(default_factory=list)
    updated_at: Optional[datetime] = None

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
        """
        Returns a string representation of the document's structure as a tree.
        Mostly for debugging purposes.
        :return: str
        """

        def _build_tree(sections, indent=0):
            tree = ""
            for sec in sections:
                if isinstance(sec, Section):
                    tree += " " * indent + f"{sec.title} (h{sec.level})\n"
                    tree += _build_tree(sec.content, indent + 2)
            return tree

        return _build_tree(self.sections)

    def print_tree(self):
        """
        Prints the document's structure as a tree.
        Mostly for debugging purposes.
        :return:
        """
        print(self.get_tree_str())
