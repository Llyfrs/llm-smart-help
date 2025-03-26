"""
This is the main file for the project.
"""
import logging
import os
import time


from dotenv import load_dotenv
from tqdm import tqdm
from transformers.models.donut.processing_donut import DonutProcessorKwargs

from src.embedding.STEmbeding import STEmbedding
from src.preprocesing.document_parsing.bullet_list import BulletList
from src.preprocesing.document_parsing.document import Document
from src.preprocesing.document_parsing.document_loader import DocumentLoader
from src.preprocesing.document_parsing.document_parser import DocumentParser
from src.preprocesing.document_parsing.paragraph import Paragraph
from src.preprocesing.document_parsing.section import Section
from src.preprocesing.document_parsing.table import Table
from src.vectordb.vector import Vector
from src.vectordb.vector_storage import VectorStorage


def get_chunks(model: STEmbedding, storage: VectorStorage):
    files = os.listdir("data")

    # Read and parse documents first
    documents = DocumentLoader(path="data", verbose=True).load()

    # Collect all chunks with their metadata
    all_chunks = []

    with tqdm(total=len(documents), desc="Processing Documents", unit="doc") as pbar:
        for document in documents:
            doc_position = 0  # Position counter for this document
            queue = [document]

            while queue:

                section = queue.pop(0)
                content = str(section)

                tokens = model.get_token_length(content)

                skipped = 0

                if tokens <= model.max_seq_length:
                    # Collect chunk data for later processing
                    all_chunks.append(
                        Vector(
                            vector=[],
                            file_name=document.file_name,
                            file_position=doc_position,
                            content=content,
                            metadata=document.metadata
                        )
                    )
                    doc_position += 1
                    continue

                # Process subsections if content is too long
                if isinstance(section, Document):
                    queue.extend(section.sections)
                elif isinstance(section, Section):
                    queue.extend(section.content)
                elif isinstance(section, Table):

                    ## This unfotunatelly does happen on smaller models
                    if len(section.rows) <= 1:
                        logging.warning(f"Skipping single row table in {document.file_name}")
                        continue

                    # Split table rows into two halves
                    rows = round(len(section.rows) /  2)
                    queue.extend([
                        Table( headers=section.headers, rows=section.rows[:rows], caption=section.caption),
                        Table( headers=section.headers, rows=section.rows[rows:], caption=section.caption)
                    ])

                elif isinstance(section, BulletList):

                    if len(section.items) == 1:
                        logging.warning(f"Skipping single item bullet list in {document.file_name}")
                        continue

                    # Split bullet list into two halves
                    items = round(len(section.items) / 2)
                    queue.extend([
                        BulletList(items=section.items[:items]),
                        BulletList(items=section.items[items:])
                    ])
                elif isinstance(section, Paragraph):
                    # Split paragraph into two halves

                    content = section.content

                    half = round(len(content) / 2)
                    queue.extend([
                        Paragraph(content=content[:half]),
                        Paragraph(content=content[half:]),
                    ])

                else:
                    print(f"Skipping {section.__class__.__name__} with {tokens} tokens")

            pbar.update(1)


    print(f"Total chunks: {len(all_chunks)}")

    exit(0)

    # Batch embed all contents at once
    if all_chunks:
        # Step 1: Extract all contents for batch embedding
        contents = [chunk.content for chunk in all_chunks]

        # Step 2: Batch embed all contents at once
        vectors = model.embed(contents)

        # Step 3: Prepare data for batch insertion
        entries = []
        for chunk, vector in zip(all_chunks, vectors):
            chunk.vector = vector.tolist()
            entries.append(chunk)

        # measure the time taken to insert the data
        start_time = time.time()

        # Step 4: Batch insert all entries
        storage.batch_insert(entries, batch_size=2000, verbose=True)  # Adjust batch_size as needed

        end_time = time.time()
        print(f"Time taken to insert data: {end_time - start_time} seconds")


if __name__ == "__main__":

    # Load the document parser


    load_dotenv()
    connection_string = os.getenv("POSTGRESQL_CONNECTION_STRING")

    model = STEmbedding("intfloat/multilingual-e5-large-instruct", cache_folder="cache")

    print("Embedding model loaded successfully!")

    table = VectorStorage(
        name="MiniLM", dimension=model.dimension, connection_string=connection_string
    )


    get_chunks(model, table)

    while True:

        querry = input("Enter the query: ")

        query_vector = model.embed([querry])[0].tolist()

        results = table.query(query_vector, n=5, distance="cosine")

        for result in results:
            print(result.file_name)
            print(result.content)
            print("-------------------")
