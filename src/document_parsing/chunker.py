import re
from typing import Callable

from typing import Literal

from src.document_parsing.chunk import Chunk
from src.document_parsing.bullet_list import BulletList
from src.document_parsing.document import Document
from src.document_parsing.paragraph import Paragraph
from src.document_parsing.section import Section
from src.document_parsing.table import Table

import tiktoken


class Chunker:

    def __init__(
        self,
        chunk_size: int,
        chunk_strategy: Literal["max_tokens", "balanced", "min_tokens"] = "max_tokens",
        tokenizer: Callable[[str], list[int]] = None,
    ):
        """
        Initialize the Chunker with a specified chunk size.
        :param chunk_size: The maximum size of each chunk
        """

        self.chunk_size = chunk_size
        self.chunk_strategy = chunk_strategy

        ## If tokenizer function is not provided we use tiktoken to estimate the size of the chunk,
        # because we are estimating we set the chunk size to 90% of the original size to avoid overflows
        if tokenizer is not None:
            self.tokenizer = tiktoken.get_encoding("cl100k_base").encode
            self.chunk_size = chunk_size if tokenizer else chunk_size * 0.90
        else:
            self.tokenizer = tokenizer

    def chunk(self, document: Document) -> list[Chunk]:

        chunks = []
        doc_position = 0  # Position counter for this document

        queue = []

        ## When balanced or maximum strategy is used we start with the full document
        ## The difference in strategy will be latter when splitting the document it's self
        if self.chunk_strategy == "max_tokens" or self.chunk_strategy == "balanced":
            queue = [document]

        ## When minimal strategy is used we flatten the content to its basics elements.
        ## This makes sure the final chunks are as small as possible while maintaining stucture
        ## Any future splitting will be done in cases of overflows
        elif self.chunk_strategy == "min_tokens":
            # Start with the root document
            queue = [document]
            processed = []

            # Process until queue is empty
            while queue:
                # Get the next item
                item = queue.pop(0)
                if isinstance(item, Document):
                    queue.extend(item.sections)
                elif isinstance(item, Section):
                    queue.extend(item.content)
                else:
                    processed.append(item)

            queue = processed

        while queue:
            section = queue.pop(0)
            content = str(section)

            ## Remove metadata from content
            if getattr(section, "metadata", None):
                content = re.sub(
                    r"^---.*?---\n?", "", content, count=1, flags=re.DOTALL
                )

            tokens = len(self.tokenizer(content))

            if tokens <= self.chunk_size:
                # Collect chunk data for later processing
                chunks.append(
                    Chunk(
                        file_name=document.file_name,
                        file_position=doc_position,
                        content=content,
                        metadata=document.metadata,
                    )
                )
                doc_position += 1
                continue

            # Process subsections if content is too long
            # We are entering this code only if the section is too long
            if isinstance(section, Document):

                ## To maximize the size of the chunks we split document in to two halves
                if self.chunk_strategy == "max_tokens":
                    # If the document is too long, split it into two halves
                    if len(section.sections) == 1:
                        queue.extend(section.sections)
                        continue

                    half = round(len(section.sections) / 2)
                    queue.extend(
                        [
                            Document(
                                file_name=document.file_name,
                                sections=section.sections[:half],
                            ),
                            Document(
                                file_name=document.file_name,
                                sections=section.sections[half:],
                            ),
                        ]
                    )
                ## If we are using balanced strategy we split the document in it's sections,
                # this will potentially result in smaller chunks that max_tokens but, makes chunks more structured
                # and still keeps them bigger than min_tokens
                else:
                    queue.extend(section.sections)

            elif isinstance(section, Section):
                """
                Sections are very similar to documents and their splitting strategy follows the same logic.
                """

                ## For explanations on the splitting strategy see the code above
                if self.chunk_strategy == "max_tokens":

                    # If the section is too long, split it into two halves
                    if len(section.content) == 1:
                        queue.extend(section.content)
                        continue

                    half = round(len(section.content) / 2)
                    queue.extend(
                        [
                            Section(
                                title=section.title,
                                level=section.level,
                                content=section.content[:half],
                            ),
                            Section(
                                title=section.title,
                                level=section.level,
                                content=section.content[half:],
                            ),
                        ]
                    )
                else:
                    queue.extend(section.content)

            elif isinstance(section, Table):

                """
                Generally we want tables to be chunked together, and only split if needed,
                with the header preserved, for bot half's for context.
                """

                ## This unfortunately does happen on smaller models
                if len(section.rows) <= 1:
                    continue

                # Split table rows into two halves
                rows = round(len(section.rows) / 2)
                queue.extend(
                    [
                        Table(
                            headers=section.headers,
                            rows=section.rows[:rows],
                            caption=section.caption,
                        ),
                        Table(
                            headers=section.headers,
                            rows=section.rows[rows:],
                            caption=section.caption,
                        ),
                    ]
                )

            elif isinstance(section, BulletList):

                """
                Same as tabel, we want to keep lists complete if possible,
                """

                if len(section.items) == 1:
                    continue

                # Split bullet list into two halves
                items = round(len(section.items) / 2)
                queue.extend(
                    [
                        BulletList(items=section.items[:items]),
                        BulletList(items=section.items[items:]),
                    ]
                )
            elif isinstance(section, Paragraph):

                """
                Same as table and bullet list.
                """

                # TODO: Consider overlapping paragraph splits to avoid damage of splitting paragraph on very important section

                content = section.content

                half = round(len(content) / 2)
                queue.extend(
                    [
                        Paragraph(content=content[:half]),
                        Paragraph(content=content[half:]),
                    ]
                )

        return chunks
