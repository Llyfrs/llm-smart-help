import os
from datetime import datetime
from typing import Literal, Any, Generator
from tqdm import tqdm

from src.document_parsing import Document, Chunker
from src.document_parsing.document_parser import DocumentParser
from src.models import EmbeddingModel
from src.vectordb.vector import Vector
from src.vectordb.vector_storage import VectorStorage


def embedding_routine(
    data_path: str,
    chunker: Chunker,
    embedding_model: EmbeddingModel,
    vector_storage: VectorStorage,
    mode: Literal["create", "update"] = "create",
):
    """
    This is a routine that loads all markdown documents from given directory and its subdirectories, creates chunks using the chunker and embeds those chunks and saves them in to the vector storage.

    :param data_path: Path to the directory containing markdown files
    :param chunker: Inicialized chunker object
    :param embedding_model: The embedding model to use for embedding the chunks
    :param vector_storage: The vector storage to use for storing the vectors
    :param mode: The mode in which to run the routine. If "create" it will empty existing vector storage and embed all files again. If "update" only new or edited files will be embedded.
    :return:

    Note: This function processes data one by one, making it save to use with large quantities of data, even if it's somewhat slower because of it.
    """

    if mode not in ["create", "update"]:
        raise ValueError("Mode must be either 'create' or 'update'.")

    if mode == "create":
        vector_storage.clear_table()

    number_of_files = sum(len(files) for _, _, files in os.walk(data_path))
    pbar = tqdm(total=number_of_files, desc="Processing files", unit="file")

    for document in _document_generator(data_path):
        chunks = chunker.chunk(document)
        contents = [chunk.content for chunk in chunks]
        embeddings = embedding_model.embed(contents)
        vectors = [
            Vector.from_chunk(chunk, embedding)
            for chunk, embedding in zip(chunks, embeddings)
        ]

        if mode == "create":
            vector_storage.batch_insert(vectors)

        elif mode == "update":
            file = vector_storage.get_file(document.file_name)
            if len(file) == 0:
                vector_storage.batch_insert(vectors)

            elif file[0].updated_at < document.updated_at:
                vector_storage.delete_file(document.file_name)
                vector_storage.batch_insert(vectors)

        pbar.update(1)

    # The directory could contain non-markdown files and those won't be returned by the document_generator
    # Yet we do process all of them so the bar should represent that by being 100%
    pbar.update(pbar.total - pbar.n)
    pbar.close()


def _document_generator(path: str) -> Generator[Document, None, None]:
    """
    Yields parsed .md documents from the given directory and its subdirectories.
    This is a helper function to lazyly load documents from disk when needed.

    :param path: The directory path to search for .md files.
    """
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)

                modified_time = os.path.getmtime(file_path)
                ## to datetime
                modified_time = datetime.fromtimestamp(modified_time)

                with open(file_path, "r") as f:
                    data = f.read()
                    document = DocumentParser(
                        file_name=file, updated_at=modified_time
                    ).parse(data)
                    yield document