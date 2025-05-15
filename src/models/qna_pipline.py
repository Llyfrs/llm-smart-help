from dataclasses import dataclass, field
from typing import List
import copy

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
        """
        🚀 Full QA pipeline from term extraction → final answer.
        Returns QAPipelineResult.
        """

        final_result = QAPipelineResult()

        EMBED_PROMPT = "Given user query and keywords, retrieve relevant passages that best answer asked question."

        qgen_prompt = ""

        if self.global_prompt != "":
            qgen_prompt += "Global Context" + self.global_prompt + "\n\n"

        for _ in range(self.max_iterations):

            # ❓ 3) Question generation
            questions_struct: Questions = self.agents.main_researcher_model.generate_response(
                prompt=qgen_prompt + f"'\noriginal_user_question': {user_query}", structure=Questions
            )

            final_result.cost += self.agents.main_researcher_model.get_cost()

            final_result.satisfactions.append(questions_struct)

            # Check if the questions are satisfied
            if questions_struct.satisfied:
                break

            final_result.iterations += 1

            # 📚 4) Question research
            question_answers: dict[str, str] = {}
            for q in questions_struct.questions:
                vec = self.embedding_model.embed([q.question_text + " " + " ".join(q.keywords)], instruction=EMBED_PROMPT)[0].tolist()
                docs = self.vector_storage.query(vec, n=10)
                ctx = "\n".join("source:" + d.file_name + "\n" + d.content for d in docs)
                ans = self.agents.query_researcher_model.generate_response(
                    prompt=f"**Context:**\n{ctx}\n\nResearched Question: {q}"
                ).strip()
                question_answers[q.question_text] = ans
                final_result.questions[q.question_text] = ans
                final_result.used_context.extend(docs)
                final_result.cost += self.agents.query_researcher_model.get_cost()

            ## Asked and answered questions
            qgen_prompt += "\n\n".join(f"---\nQuestion: {q}\nAnswer: {a}\n---" for q, a in question_answers.items())

        # 🏁 5) Final answer
        final_context = f"{qgen_prompt}\n\nUser Query: {user_query}"
        final_answer = self.agents.main_model.generate_response(prompt=final_context).strip()

        final_result.cost += self.agents.main_model.get_cost()

        final_result.final_answer = final_answer

        return final_result

    def __copy__(self):
        """
        Creates a shallow copy of QAPipeline.
        """
        return QAPipeline(
            agents=copy.copy(self.agents),
            embedding_model=copy.copy(self.embedding_model),
            vector_storage=self.vector_storage,
            global_prompt=self.global_prompt,
            max_iterations=self.max_iterations,
        )
