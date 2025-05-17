from dataclasses import dataclass, field
from typing import List
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    cost: float = field(default_factory=float)
    final_answer: str = ""


def process_question(q, embed_prompt, embedding_model, vector_storage, researcher_model):
    vec = embedding_model.embed([
        q.question_text + " " + " ".join(q.keywords)
    ], instruction=embed_prompt)[0].tolist()
    docs = vector_storage.query(vec, n=10)
    ctx = "\n".join("source:" + d.file_name + "\n" + d.content for d in docs)
    ans = researcher_model.generate_response(
        prompt=f"**Context:**\n{ctx}\n\nResearched Question: {q}"
    ).strip()
    cost = researcher_model.get_cost()
    return q.question_text, ans, docs, cost


class QAPipeline:
    def __init__(
        self,
        agents: Agents,
        embedding_model: EmbeddingModel,
        vector_storage: VectorStorage,
        global_prompt: str = "",
        max_iterations: int = 5,
    ):
        self.agents = agents
        self.embedding_model = embedding_model
        self.vector_storage = vector_storage
        self.global_prompt = global_prompt
        self.max_iterations = max_iterations

    def run(self, user_query: str) -> QAPipelineResult:
        final_result = QAPipelineResult()

        EMBED_PROMPT = "Given user query and keywords, retrieve relevant passages that best answer asked question."
        qgen_prompt = ""

        if self.global_prompt:
            qgen_prompt += "Global Context: " + self.global_prompt + "\n\n"

        for _ in range(self.max_iterations):
            questions_struct: Questions = self.agents.main_researcher_model.generate_response(
                prompt=qgen_prompt + f"'\noriginal_user_question': {user_query}", structure=Questions
            )

            final_result.cost += self.agents.main_researcher_model.get_cost()
            final_result.satisfactions.append(questions_struct)

            if questions_struct.satisfied:
                break

            final_result.iterations += 1

            embedding_model_copy = copy.copy(self.embedding_model)
            researcher_model_copy = copy.copy(self.agents.query_researcher_model)
            vector_storage = self.vector_storage  # assumed read-only

            question_answers = {}
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        process_question,
                        q,
                        EMBED_PROMPT,
                        embedding_model_copy,
                        vector_storage,
                        researcher_model_copy
                    )
                    for q in questions_struct.questions
                ]

                for future in as_completed(futures):
                    q_text, ans, docs, cost = future.result()
                    question_answers[q_text] = ans
                    final_result.questions[q_text] = ans
                    final_result.used_context.extend(docs)
                    final_result.cost += cost

            qgen_prompt += "\n\n".join(f"---\nQuestion: {q}\nAnswer: {a}\n---" for q, a in question_answers.items())

        final_context = f"{qgen_prompt}\n\nUser Query: {user_query}"
        final_answer = self.agents.main_model.generate_response(prompt=final_context).strip()

        final_result.cost += self.agents.main_model.get_cost()
        final_result.final_answer = final_answer

        return final_result

    def __copy__(self):
        return QAPipeline(
            agents=copy.copy(self.agents),
            embedding_model=copy.copy(self.embedding_model),
            vector_storage=self.vector_storage,
            global_prompt=self.global_prompt,
            max_iterations=self.max_iterations,
        )
