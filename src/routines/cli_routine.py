from typing import Type

from src.models import LLModel, EmbeddingModel
from src.models.agents import Agents
from src.models.structured_output.questions import Questions
from src.models.structured_output.terms import Terms
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


def run_qa_pipeline(
    user_query: str,
    agents: Agents,
    embedding_model: EmbeddingModel,
    vector_storage: VectorStorage,
) -> tuple[str, str]:
    """
    🚀 Full QA pipeline from term extraction → final answer.
    Returns (final_context, final_answer).
    """
    EMBED_PROMPT = "Give user query, retrieve relevant passages that best answer asked question."

    # 🔍 1) Term extraction
    terms_struct: Terms = agents.term_extraction_model.generate_response(
        prompt=user_query, structure=Terms
    )

    # 📝 2) Term research
    term_explanations: dict[str, str] = {}
    for term in terms_struct.terms:
        vec = embedding_model.embed([f"What is {term}?"], instruction=EMBED_PROMPT)[0].tolist()
        docs = vector_storage.query(vec, n=3)
        context = "".join(c.content for c in docs)
        explanation = agents.term_researcher_model.generate_response(
            prompt=f"Explain the term {term} based on:\n\n{context}"
        ).strip()
        term_explanations[term] = explanation

    # 🔗 Build context for question generation
    terms_block = "\n".join(f"{t}: {e}" for t, e in term_explanations.items())
    qgen_prompt = f"**Context**\n{terms_block}\n\nUser Query: {user_query}"

    # ❓ 3) Question generation
    questions_struct: Questions = agents.query_generator_model.generate_response(
        prompt=qgen_prompt, structure=Questions
    )

    # 📚 4) Question research
    question_answers: dict[str, str] = {}
    for q in questions_struct.questions:
        vec = embedding_model.embed([q], instruction=EMBED_PROMPT)[0].tolist()
        docs = vector_storage.query(vec, n=3)
        ctx = "\n".join(d.content for d in docs)
        ans = agents.query_researcher_model.generate_response(
            prompt=f"**Context:**\n{ctx}\n\nResearched Question: {q}"
        ).strip()
        question_answers[q] = ans

    # 🏁 5) Final answer
    qa_block = "\n\n".join(f"Question: {q}\nAnswer: {a}" for q, a in question_answers.items())
    final_context = f"**Context**\n{qa_block}\n\nUser Query: {user_query}"
    final_answer = agents.main_model.generate_response(prompt=final_context).strip()

    final_context = f"{terms_block}\n\n" + final_context
    return final_context, final_answer


# Updated cli_routine
def cli_routine(
    agents: Agents,
    embedding_model: EmbeddingModel,
    vector_storage: VectorStorage,
):
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        final_ctx, answer = run_qa_pipeline(
            user_query=user_input,
            agents=agents,
            embedding_model=embedding_model,
            vector_storage=vector_storage,
        )

        print(colored_text(f"Final Context: {final_ctx}", "blue"))
        print(colored_text(f"Final Answer: {answer}", "green"))
        break


