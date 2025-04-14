from typing import Type

from src.models import LLModel, EmbeddingModel
from src.models.structured_output.terms import Terms
from src.vectordb.vector_storage import VectorStorage

MAIN_MODEL_PROMPT = """
You are a helpful assistant. Answer the user's questions based on the provided context.
Keep answers short and formated in way that is easy to read in console application. Don't use markdown."
""".strip()


TERMS_EXTRACTION_PROMPT = """

Extract terms or entities directly from the text by following these guidelines: 
Use the exact wording from the original text, making only necessary corrections to obvious spelling mistakes. 
By default, represent each term as a single word; however, if the term clearly constitutes a multi-word entity, such as a proper noun (e.g., "New York"), retain it as such. 
Additionally, ensure that words that are clearly descrititve adjectives (e.g., "red", "big") are included with term they are describing as one. (e.g., "red apple" should be represented as a single term "red apple").
Finally, normalize each term to its base or root form (for example, converting "running" to "run") and output the resulting list of extracted terms.

""".strip()

TERM_RESEARCHER_PROMPT = """

You are a unpaid intern at a company and your job is to take raw data and extract definition of a single term from it.
You output should be 2 to 3 sentence conveying the meaning of the term. Grammar, flowery sentences and punctuation are not important, but the meaning should be clear.
These summaries will be latter used by other interns to add context to existing texts using these terms.

""".strip()

def colored_text(text: str, color: str) -> str:
    """
    Return a string with ANSI escape codes for colored text.
    :param text: The text to color.
    :param color: The color to use. Options are 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'.
    :return: The colored text.
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, colors['reset'])}{text}{colors['reset']}"


def cli_routine(
    model: LLModel,
    embedding_model: EmbeddingModel,
    vector_storage: VectorStorage,
):
    """
    Chat with your data!
    :param model:
    :param embedding_model:
    :param vector_storage:
    :return:
    """


    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        prompt = "Give user query, retrieve relevant passages that best answer asked question."

        model.system_prompt = TERMS_EXTRACTION_PROMPT
        response = model.generate_response(prompt=user_input, structure=Terms)

        print(colored_text(f"Terms: {response}", "green"))

        model.system_prompt = TERM_RESEARCHER_PROMPT

        for term in response.terms:
            print(colored_text(f"Term: {term}", "yellow"))
            context = vector_storage.query(embedding_model.embed([f"Explain the term {term}"], instruction=prompt)[0].tolist(), n=1)
            print(colored_text(f"Context: {context[0].content}", "blue"))
            response = model.generate_response(prompt=context[0].content)
            print(colored_text(f"Definition: {response}", "green"))




        # relevant_docs = vector_storage.query(embedding_model.embed([user_input], instruction=prompt)[0].tolist(), n=5)

        # context = "\n\n".join(doc.content for doc in relevant_docs)

        # print(colored_text(f"{context}", "red"))

        # context += "\n\nUser Question:" + user_input

        # Generate a response using the model


        #print(f"{colored_text(f'Assistant: {response}', 'green')}")