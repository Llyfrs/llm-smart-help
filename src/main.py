"""
This is the main file for the project.
"""
import os
from dataclasses import dataclass, field
from typing import List, Any, Dict, Union

import numpy as np
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from tqdm import tqdm
from src.embedding.STEmbeding import STEmbedding

from markdown_it import MarkdownIt
import re

## h1 > h2 > h3 > h4 > h5 > h6
def comp_tags(tag1 :str , tag2: str):
    tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
    return tags.index(tag1) - tags.index(tag2)

def decode_inline(tokens: List[SyntaxTreeNode]) -> str:

    # print(tokens)

    if tokens is None:
        return ""

    text = ""

    for token in tokens:
        text += re.sub(r'\s+', ' ', token.content)

        if token.type == "softbreak":
            text += "\n"


    return text

@dataclass
class Paragraph:
    content: str

    def __str__(self) -> str:
        return self.content

@dataclass
class Table:
    caption: str
    headers: List[str]
    rows: List[List[str]]

    def __str__(self) -> str:
        """
        Returns markdown representation of the table
        :return:
        """

        table = f"{self.caption}:\n\n"
        table +=  "|" + "|".join(self.headers) + "|\n"
        table += "|" + "|".join(["---" for _ in self.headers]) + "|\n"

        for row in self.rows:
            table += "|" + "|".join(row) + "| \n"

        return table

    def parse(self, paragraph : SyntaxTreeNode) -> None:

        string = decode_inline(paragraph.children[0].token.children)

        lines = string.split("\n")

        self.headers = [header.strip() for header in lines[0].split("|") if len(header.strip()) > 0]

        self.rows = []

        for line in lines[2:]:
            self.rows.append([cell.strip() for cell in line.split("|") if len(cell.strip()) > 0])

        pass

@dataclass
class Image:
    url: str
    alt: str

    def __str__(self) -> str:
        return f"![{self.alt}]({self.url})"

    def parse(self, root):
        pass


@dataclass
class BulletList:
    items: List[str]

    def __str__(self) -> str:
        bullet_list = ""
        for item in self.items:
            bullet_list += f"- {item}\n"

        return bullet_list

@dataclass
class Section:
    title: str
    level: int
    content: List[Union[Paragraph, Table, "Section", Image, BulletList]] = field(default_factory=list)

    def __str__(self) -> str:
        section = "#" * self.level + f" {self.title}\n\n"
        for content in self.content:
            section += str(content)
        return section  # Ensure the section string is returned

    def parse(self, root : List[SyntaxTreeNode] ):
        i = 0
        while i < len(root):

            child = root[i]

            # print(child.type)

            if child.type == "heading":
                level = child.tag
                start_index = i + 1  # Start right after the current heading
                end_index = start_index
                # Collect until next heading of same or higher level
                while end_index < len(root):
                    current = root[end_index]
                    if current.type == "heading":
                        current_level = current.tag
                        # Assuming comp_tags returns 0 for same, >0 for deeper, <0 for higher
                        if comp_tags(current_level, level) <= 0:
                            break
                    end_index += 1
                # Extract children from start_index to end_index-1
                children = root[start_index:end_index]
                # Create section and parse its children recursively
                self.content.append(
                    Section(decode_inline(child.children[0].token.children), self.level + 1).parse(children))
                # Skip processed elements in outer loop
                i = end_index - 1  # Adjust outer index to avoid reprocessing


            if child.type == "paragraph":

                ##print(child.children[0].content)

                if child.children[0].content.startswith("|"):

                    caption = root[i-1].children[0].content
                    table = Table(caption, [], [])
                    table.parse(child)
                    self.content.append(table)

                    pass

                else:
                    self.content.append(Paragraph(decode_inline(child.children[0].token.children)))

                pass


            if child.type == "bullet_list":
                pass

            i+=1


        return self
        pass


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

    def parse(self, document: str) -> "Document":
        """
        This function parses a document string into a Document object
        :param document:
        :return:
        """

        # Extract metadata if present
        metadata_dict = {}
        if document.startswith("---"):
            end = document.find("---", 3)
            if end != -1:
                metadata_text = document[3:end].strip()
                document = document[end + 3:]

                # Parse metadata into dictionary
                metadata_dict = {
                    key.strip(): value.strip()
                    for line in metadata_text.split("\n")
                    if ":" in line
                    for key, value in [line.split(":", 1)]
                }

        self.metadata = metadata_dict

        root = SyntaxTreeNode(MarkdownIt().parse(document))

        # print(root.pretty())

        section = Section(self.file_name, 0)
        section.parse(root.children)

        self.sections = section.content

        return self




def header_level(line: str) -> int:
    if line.startswith("#"):
        return len(line.split(" ")[0])
    return 0





if __name__ == '__main__':

    # file = "../data/Ammo -  Torncity WIKI - The official help and support guide.md"
    file = "../data/Pickpocketing -  Torncity WIKI - The official help and support guide.md"

    with open(file, 'r') as f:
        data = f.read()

    document = Document("Pickpocketing").parse(data)

    print(document)

    exit(0)

    chunks = create_chunks("../data/Pickpocketing -  Torncity WIKI - The official help and support guide.md")

    for chunk in chunks:
        print(chunk)


    exit(0)

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
                data = f.read()

                data = data.split("\n")

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


