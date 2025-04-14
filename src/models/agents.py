from dataclasses import dataclass

from src.models import LLModel


@dataclass
class Agents:
    main : LLModel = None
    term_extractor : LLModel = None
    term_researcher : LLModel = None
    query_generator : LLModel = None
    query_researcher : LLModel = None
    judge: LLModel = None