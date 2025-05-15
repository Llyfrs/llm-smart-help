import csv
import copy
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm
from src.models.qna_pipline import QAPipeline




def load_csv(path: str):
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def save_csv(path: str, data: list[dict]):
    with open(path, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in data:
            writer.writerow(row)


def process_question(entry, qan : QAPipeline):
    try:

        answ = qan.run(user_query=entry["query"])
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
    except Exception as e:
        entry["answer"] = ""
        entry["full_context"] = f"Error generating answer: {e}"
        entry["cost"] = ""
        entry["iterations"] = ""

    return entry


def generate_answers(
        path: str,
        qan: QAPipeline,
        max_workers: int = 10,
):
    questions = load_csv(path)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                process_question,
                entry=copy.deepcopy(entry),  # Avoid shared mutation
                qan=copy.copy(qan)
            )
            for entry in questions
        ]

        for f in tqdm(as_completed(futures), total=len(futures), desc="Generating answers", unit="q"):
            results.append(f.result())

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = path.rsplit(".", 1)[0] + f"_answers_{timestamp}.csv"
    save_csv(out_file, results)

    return out_file
