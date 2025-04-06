"""
This is the main file for the project.
"""
import os
import time

import toml


from tqdm import tqdm

from src.models import OAEmbedding, EmbeddingModel
from src.models.st_embedding import STEmbedding
from src.models.llmodel import LLModel
from src.document_parsing import Chunker

from src.document_parsing.document_parser import DocumentParser
from src.structured_output.terms import Terms
from src.vectordb.vector import Vector
from src.vectordb.vector_storage import VectorStorage


def get_chunks(model: EmbeddingModel, storage: VectorStorage):
    files = os.listdir("data")

    # Read and parse documents first
    documents = []

    # Set up tqdm with conditional verbosity
    progress_bar = tqdm(enumerate(files, 1), desc="Reading Files", unit="file")

    for i, file in progress_bar:
        file_path = os.path.join("data", file)

        with open(file_path, "r") as f:
            data = f.read()
            document = DocumentParser(file_name=file).parse(data)
            documents.append(document)

    # Collect all chunks with their metadata
    all_chunks = []

    chunker = Chunker(chunk_size=model.dimension, chunk_strategy="max_tokens", tokenizer=model.tokenize)

    with tqdm(total=len(documents), desc="Processing Documents", unit="doc") as pbar:
        for document in documents:
            all_chunks.extend(chunker.chunk(document))
            pbar.update(1)


    print(f"Total chunks: {len(all_chunks)}")

    # Batch embed all contents at once
    if len(all_chunks) == 0:
        print("No chunks we created.")
        return


    # Step 1: Extract all contents for batch embedding
    contents = [chunk.content for chunk in all_chunks]

    batch_size = 100
    vectors = []
    with tqdm(total=len(contents), desc="Embedding Contents", unit="content") as pbar:
        for i in range(0, len(contents), batch_size):
            batch = contents[i:i + batch_size]
            vectors.extend(model.embed(batch))
            pbar.update(len(batch))

    # Step 3: Prepare data for batch insertion
    entries = []
    for chunk, vector in zip(all_chunks, vectors):
        v = Vector.from_chunk(chunk, vector.tolist())
        entries.append(v)

    # measure the time taken to insert the data
    start_time = time.time()

    # Step 4: Batch insert all entries
    storage.batch_insert(entries, batch_size=2000, verbose=True)  # Adjust batch_size as needed

    end_time = time.time()
    print(f"Time taken to insert data: {end_time - start_time} seconds")


if __name__ == "__main__":


    # Load the document parser

    toml_file = "config.toml"
    config = toml.load(toml_file)

    connection_string = config["POSTGRESQL_CONNECTION_STRING"]

    model = STEmbedding("intfloat/multilingual-e5-large-instruct")

    print("Embedding model loaded successfully!")

    table = VectorStorage(
        name="MiniLM", dimension=model.dimension, connection_string=connection_string
    )


    llmodel = LLModel(
        model_name=config["model"][list(config["model"].keys())[0]]["MODEL_NAME"],
        endpoint=config["model"][list(config["model"].keys())[0]]["ENDPOINT_URL"],
        api_key=config["model"][list(config["model"].keys())[0]]["API_KEY"],
        system_prompt="Based on provided context, answer the question.",
    )

    print("LLM model loaded successfully!")


    # get_chunks(model, table)

    def get_detailed_instruct(task_description: str, query: str) -> str:
        return f'Instruct: {task_description}\nQuery: {query}'


    while True:

        query = input("Enter the query: ")

        query = get_detailed_instruct("Given provided query, retrieve documents that best answer asked question.", query)

        query_vector = model.embed([query])[0].tolist()

        results = table.query(query_vector, n=5, distance="cosine")

        context = "Context:\n\n"
        for result in results:
            context += result.content + "\n\n"


        # print(f"Context: {context}")

        context += "Question:\n\n"

        llmodel_response = llmodel.generate_response(prompt=context + query)

        print(f"LLM Response: {llmodel_response}")