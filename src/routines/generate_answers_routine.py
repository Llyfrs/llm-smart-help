import csv
from datetime import datetime

from tqdm import tqdm

from src.models import EmbeddingModel
from src.models.agents import Agents
from src.routines.qa_pipeline import run_qa_pipeline
from src.vectordb.vector_storage import VectorStorage


def load_csv(path : str):
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)

    return data

def save_csv(path : str, data : list[dict]):
    with open(path, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in data:
            writer.writerow(row)


def generate_answers(
        path: str,
        agents: Agents,
        embedding_model: EmbeddingModel,
        vector_storage: VectorStorage,
    ):
    questions = load_csv(path)

    for entry in tqdm(questions, desc="Generating answers", unit="q"):
        try:
            answ = run_qa_pipeline(
                user_query=entry["query"],
                agents=agents,
                embedding_model=embedding_model,
                vector_storage=vector_storage,
            )
        except Exception as e:
            print(f"Error generating answer for query '{entry['query']}': {e}")
            break

        entry["answer"] = answ.final_answer

        parts = []
        for term, explanation in answ.terms.items():
            parts.append(f"Term: {term}")
            parts.append(f"Explanation: {explanation}")

        for sat in answ.satisfactions:
            parts.append(f"Satisfied Reason: {sat.satisfied_reason}")
            parts.append(f"Question Response: {sat.reasoning}")
            for q in sat.questions:
                answer_text = answ.questions.get(q.question_text, "")
                parts.append(f"Question: {q.question_text}")
                parts.append(f"Keywords: {q.keywords}")
                parts.append(f"Answer: {answer_text}")

        entry["full_context"] = "\n".join(parts)
        entry["cost"] = answ.cost
        entry["iterations"] = answ.iterations

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = path.rsplit(".", 1)[0] + f"_answers_{timestamp}.csv"
    save_csv(out_file, questions)

    return out_file