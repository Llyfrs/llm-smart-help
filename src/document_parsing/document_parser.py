import re
from typing import List, Union, Dict

from black import datetime
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from .bullet_list import BulletList
from .document import Document
from .image import Image
from .paragraph import Paragraph
from .section import Section
from .table import Table


class DocumentParser:
    """
    Parses a markdown document into a Document object.

    This class centralizes the parsing logic for handling markdown files, keeping the
    logic simple and delegating actual data storage to the Section, Table, and other
    data-holder classes.

    :param file_name: The name of the markdown file being parsed.
    :type file_name: str

    .. code-block:: python
        with open("file.md", "r") as f:
            data = f.read()
            parser = DocumentParser(file_name="file.md")
            document = parser.parse(data)
            print(document)  # Print the document as markdown

    """

    def __init__(self, file_name: str, updated_at: datetime = None):
        self.file_name = file_name
        self.updated_at = updated_at

    def parse(self, document: str) -> Document:
        """

        Parses a Markdown document into a Document object.

        Takes a string of markdown content and generates a Document object with metadata and content. This content can
        be of multiple types, including sections, paragraphs, tables, images, and bullet lists. And it will be nested
        in a way that corresponds to the structure of the markdown document.

        :param document:

        :return document: The parsed document object.
        :rtype: Document
        """

        # Extract metadata if present
        metadata: Dict[str, str] = {}
        if document.startswith("---"):
            end = document.find("---", 3)
            if end != -1:
                metadata_text = document[3:end].strip()
                document = document[end + 3 :]
                metadata = {
                    key.strip(): value.strip()
                    for line in metadata_text.split("\n")
                    if ":" in line
                    for key, value in [line.split(":", 1)]
                }

        # Parse markdown into a syntax tree
        md_parser = MarkdownIt()
        tokens = md_parser.parse(document)
        root = SyntaxTreeNode(tokens)

        # Parse content recursively from the syntax tree tokens
        content = self._parse_nodes(root.children)
        return Document(
            file_name=self.file_name,
            metadata=metadata,
            sections=content,
            updated_at=self.updated_at,
        )

    def _parse_nodes(
        self, nodes: List[SyntaxTreeNode]
    ) -> List[Union[Section, Paragraph, Table, Image, BulletList]]:
        """
        Recursively parses a list of syntax tree nodes into a list of document components.
        """
        result: List[Union[Section, Paragraph, Table, Image, BulletList]] = []
        i = 0

        while i < len(nodes):
            node = nodes[i]
            if node.type == "heading":
                # Create a new Section using heading level and title
                level = int(node.tag[-1])
                title = self._decode_inline(node.children[0].token.children)
                # Gather nodes that belong to this section (until a heading of same/higher level)
                j = i + 1
                sub_nodes = []
                while j < len(nodes):
                    next_node = nodes[j]
                    if next_node.type == "heading" and int(next_node.tag[-1]) <= level:
                        break
                    sub_nodes.append(next_node)
                    j += 1
                # Recursively parse sub-nodes
                section_content = self._parse_nodes(sub_nodes)
                section = Section(title=title, level=level, content=section_content)
                result.append(section)
                i = j
            elif node.type == "paragraph":
                text = self._decode_inline(node.children[0].token.children)
                # Check if it's a table (markdown tables often start with a pipe)
                if text.startswith("|"):

                    # This is the ugliest code of this parser, we check previous node and use it as a table caption.
                    # This is very specific to my use case and in most cases will provide nonsense caption.
                    # Even in that case, at least it provides context.

                    try:
                        caption = (
                            self._decode_inline(nodes[i - 1].children[0].token.children)
                            if i > 0 and nodes[i - 1].children
                            else ""
                        )
                    except:
                        caption = ""

                    lines = text.split("\n")
                    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
                    # Assume the separator row is the second line and skip it
                    rows = [
                        [cell.strip() for cell in line.split("|") if cell.strip()]
                        for line in lines[2:]
                    ]
                    table = Table(caption=caption, headers=headers, rows=rows)
                    result.append(table)
                else:
                    paragraph = Paragraph(content=text)
                    result.append(paragraph)
                i += 1
            elif node.type == "bullet_list":

                children = node.children
                items = self._collect_list(children)

                bullet_list = BulletList(items)
                result.append(bullet_list)

                i += 1
            else:
                i += 1  # Skip unhandled node types
        return result

    def _collect_list(self, children: [SyntaxTreeNode]):
        result = []
        for child in children:
            if child.type == "list_item":
                result.extend(self._collect_list(child.children))
            elif child.type == "bullet_list":
                result.extend(self._collect_list(child.children))
            elif child.type == "ordered_list":
                result.extend(self._collect_list(child.children))
            elif child.type == "paragraph":
                result.append(
                    self._decode_inline(child.children[0].token.children)
                    if child.children[0].token.children
                    else ""
                )

        return result

    @staticmethod
    def _comp_tags(tag1: str, tag2: str):
        tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
        return tags.index(tag1) - tags.index(tag2)

    @staticmethod
    def _decode_inline(tokens: List[SyntaxTreeNode]) -> str:

        if tokens is None:
            return ""

        text = ""

        for token in tokens:
            text += re.sub(r"\s+", " ", token.content)

            if token.type == "softbreak":
                text += "\n"

        return text
