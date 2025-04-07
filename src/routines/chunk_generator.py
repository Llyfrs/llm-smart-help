import os
from typing import Literal, Any, Generator
from blib2to3.pgen2.tokenize import Callable

from src.document_parsing import Document
from src.document_parsing.document_parser import DocumentParser


def chunk_generator(chunk_size: int, chunking_strategy: Literal["max_tokens", "balanced", "min_tokens"] = "balanced", tokenizer: Callable[[str], list[int]] = None):

    pass




def document_generator(path: str) -> Generator[Document, None, None]:
    """
    Yields parsed .md documents from the given directory and its subdirectories.

    :param path: The directory path to search for .md files.
    """
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)

                modified_time = os.path.getmtime(file_path)

                with open(file_path, "r") as f:
                    data = f.read()
                    document = DocumentParser(file_name=file).parse(data)
                    yield document