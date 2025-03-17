"""
This is the main file for the project.
"""
import os
import numpy as np
from tqdm import tqdm
from src.embedding.STEmbeding import STEmbedding

if __name__ == '__main__':
    model = STEmbedding('sentence-transformers/paraphrase-MiniLM-L6-v2')
    print("Embedding model loaded successfully!")

    print(model.metadata())

    vectors = []  # Store embedding vectors
    text_data = []  # Store the corresponding text content

    # Get all files and calculate total lines for accurate progress tracking
    total_lines = 0
    files = os.listdir("data")
    for file in files:
        with open(os.path.join("data", file), 'r') as f:
            total_lines += len(f.readlines())

    # Process files with a nice progress bar
    with tqdm(total=total_lines, desc="Processing data", unit="lines") as pbar:
        for file in files:
            with open(os.path.join("data", file), 'r') as f:
                data = f.read().split("\n")

                filtered_data = [line.strip() for line in data if len(line.strip()) > 0]  # Filter out empty lines

                # Store the original text
                text_data.extend(filtered_data)

                # Embed the data
                vectors.extend(model.embed(filtered_data))

                pbar.update(len(data))

    # Convert list to numpy array only once, more efficient
    vectors = np.vstack(vectors)

    print(f"Processed {len(vectors)} text segments into embeddings of shape {vectors.shape}")

    # Process query with its own progress bar
    query = ["What is the best weapon in the game?", "How do I get more gold?", "What is the best way to level up?"]

    with tqdm(total=len(query), desc="Processing queries", unit="query") as pbar:
        query_vectors = model.embed(query)
        pbar.update(len(query))

    # Calculate similarities
    print("Calculating similarities...")
    results = np.dot(vectors, query_vectors.T)  # Transpose to get proper shape for matrix multiplication

    # Display top results for each query
    for i, q in enumerate(query):
        print(f"\nTop 5 results for query: '{q}'")
        top_indices = np.argsort(results[:, i])[-5:][::-1]  # Get top 5 indices
        for idx in top_indices:
            # Show score and text (truncated if longer than 100 chars)
            text = text_data[idx]
            display_text = text[:100] + "..." if len(text) > 100 else text
            print(f"Score: {results[idx, i]:.4f} | Text: {display_text}")