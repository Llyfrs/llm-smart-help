import os

from tqdm import tqdm

from src.preprocesing.document_parsing.document_parser import DocumentParser

class DocumentLoader:
    def __init__(self, path, verbose=False):
        self.path = path
        self.verbose = verbose

    def load(self):
        """
        Load all documents from the given path.
        :return: List of parsed documents
        """

        files = os.listdir(self.path)

        # Read and parse documents first
        documents = []

        # Set up tqdm with conditional verbosity
        progress_bar = tqdm(enumerate(files, 1), desc="Reading Files", unit="file", disable=not self.verbose)

        for i, file in progress_bar:
            file_path = os.path.join(self.path, file)

            with open(file_path, "r") as f:
                data = f.read()
                document = DocumentParser(file_name=file).parse(data)
                documents.append(document)

        return documents

