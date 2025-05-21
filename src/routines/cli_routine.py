from typing import Type

from src.models import EmbeddingModel
from src.models.agents import Agents
from src.models.qna_pipline import QAPipeline
from src.vectordb.vector_storage import VectorStorage



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


# Updated cli_routine
def cli_routine(
    qna : QAPipeline
):

    """
    Command Line Interface (CLI) routine for interacting with the QAPipeline.
    :param qna:
    :return:
    """

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        answer = qna.run(user_input)

        for contex in answer.used_context:
            print(colored_text(f"\nSource: {contex.file_name}", "blue"))

        for desision in answer.satisfactions:
            print(colored_text(f"\nSatisfied Reason: {desision.satisfied_reason}", "cyan"))
            print(colored_text(f"\nQuestion Reason: {desision.reasoning}", "cyan"))

            for question in desision.questions:
                print(colored_text(f"Question: {question.question_text}", "magenta"))
                print(colored_text(f"Keywords: {question.keywords}", "yellow"))
                print(colored_text(f"Answer: {answer.questions[question.question_text]}", "white"))

        print(colored_text(f"Cost: ${answer.cost}", "red"))
        print(colored_text(f"Iterations: {len(answer.satisfactions)}", "green"))

        print(colored_text(f"Final Answer: {answer.final_answer}", "green"))
