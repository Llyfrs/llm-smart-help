import asyncio
import copy

from aiohttp import web
import json

from src.models import EmbeddingModel
from src.models.agents import Agents
from src.routines.qa_pipeline import run_qa_pipeline
from src.vectordb.vector_storage import VectorStorage

_agents: Agents
_embedding_model: EmbeddingModel
_vector_storage: VectorStorage
_global_prompt: str = ""

async def handle_request(request):
    """
    Processes incoming request and answers it using the QA pipeline, if the request is valid.
    :param request:
    :return:
    """

    try:
        data = await request.json()
        user_query = data.get("query")
        iterations = data.get("iterations", 5)

        if not user_query:
            return web.json_response({"error": "Missing 'query' field"}, status=400)

        answer = await asyncio.to_thread(
            run_qa_pipeline,
            user_query=user_query,
            agents=copy.copy(_agents),
            embedding_model=_embedding_model,
            vector_storage=_vector_storage,
            global_prompt=_global_prompt,
            max_iterations=iterations,
        )

        response_data = {
            "terms": {term: explanation for term, explanation in answer.terms.items()},
            "satisfactions": [
                {
                    "satisfied_reason": s.satisfied_reason,
                    "reasoning": s.reasoning,
                    "questions": [
                        {
                            "question": q.question_text,
                            "keywords": q.keywords,
                            "answer": answer.questions[q.question_text]
                        } for q in s.questions
                    ]
                } for s in answer.satisfactions
            ],
            "cost": answer.cost,
            "iterations": answer.iterations,
            "used_context":[
                {
                    "file_name": c.file_name,
                    "metadata": c.metadata,
                } for c in answer.used_context
            ],
            "final_answer": answer.final_answer
        }

        return web.json_response(response_data)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

def run_server(agents, embedding_model, vector_storage, global_prompt , address="127.0.0.1", port=8080):
    """
    Starts server that listens for incoming requests and processes them using the QA pipeline.
    :param agents:  Agents object containing all the models.
    :param embedding_model:  Embedding model used for vectorization.
    :param vector_storage:  Vector storage object used for storing and retrieving vectors.
    :param address: Web server address.
    :param port: Web server port.
    :return:
    """

    global _agents, _embedding_model, _vector_storage, _global_prompt
    _agents = agents
    _embedding_model = embedding_model
    _vector_storage = vector_storage
    _global_prompt = global_prompt

    app = web.Application()
    app.router.add_post("/query", handle_request)
    web.run_app(app, host=address, port=port)
