from dataclasses import dataclass, field
from typing import List

from src.models import EmbeddingModel
from src.models.agents import Agents
from src.models.structured_output.questions import Questions
from src.models.structured_output.terms import Terms
from src.vectordb.vector import Vector
from src.vectordb.vector_storage import VectorStorage


@dataclass
class QAPipelineResult:
    terms: dict[str, str] = field(default_factory=dict)
    satisfactions: List[Questions] = field(default_factory=list)
    questions: dict[str, str] = field(default_factory=dict)
    used_context: List[Vector] = field(default_factory=list)
    iterations: int = field(default_factory=int)
    cost : float = field(default_factory=float)
    final_answer: str = ""


def run_qa_pipeline(
    user_query: str,
    agents: Agents,
    embedding_model: EmbeddingModel,
    vector_storage: VectorStorage,
    global_prompt: str = "",
    max_iterations: int = 5,
) -> QAPipelineResult:
    """
    🚀 Full QA pipeline from term extraction → final answer.
    Returns (final_context, final_answer).
    """

    final_result = QAPipelineResult()

    EMBED_PROMPT = "Given user query and keywords, retrieve relevant passages that best answer asked question."



    """
    
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
        final_result.terms[term] = explanation
        final_result.used_context.extend(docs)
        final_result.cost += agents.term_researcher_model.get_cost()
    


    # 🔗 Build context for question generation
    terms_block = "\n".join(f"{t}: {e}" for t, e in term_explanations.items())
    """

    qgen_prompt = ""

    if global_prompt != "":
        qgen_prompt += "Global Context" + global_prompt + "\n\n"

    for _ in range(max_iterations):

        final_result.iterations += 1

        # ❓ 3) Question generation
        questions_struct: Questions = agents.main_researcher_model.generate_response(
            prompt=qgen_prompt + f"'\noriginal_user_question': {user_query}", structure=Questions
        )

        final_result.cost += agents.main_researcher_model.get_cost()

        final_result.satisfactions.append(questions_struct)

        # Check if the questions are satisfied
        if questions_struct.satisfied:
            break

        # 📚 4) Question research
        question_answers: dict[str, str] = {}
        for q in questions_struct.questions:
            vec = embedding_model.embed([q.question_text + " " + " ".join(q.keywords)], instruction=EMBED_PROMPT)[0].tolist()
            docs = vector_storage.query(vec, n=10)
            ctx = "\n".join("source:" + d.file_name + "\n" + d.content for d in docs)
            ans = agents.query_researcher_model.generate_response(
                prompt=f"**Context:**\n{ctx}\n\nResearched Question: {q}"
            ).strip()
            question_answers[q.question_text] = ans
            final_result.questions[q.question_text] = ans
            final_result.used_context.extend(docs)
            final_result.cost += agents.query_researcher_model.get_cost()

        ## Asked and answered questions
        qgen_prompt += "\n\n".join(f"---\nQuestion: {q}\nAnswer: {a}\n---" for q, a in question_answers.items())

    # 🏁 5) Final answer
    final_context = f"{qgen_prompt}\n\nUser Query: {user_query}"
    final_answer = agents.main_model.generate_response(prompt=final_context).strip()

    final_result.cost += agents.main_model.get_cost()

    final_result.final_answer = final_answer

    return final_result
