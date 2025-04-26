from pydantic import BaseModel, Field,Extra
from typing import List


# 1. Define the structure for a single question with keywords
class Question(BaseModel):
    """Represents a single follow-up question with associated keywords."""
    question_text: str = Field(
        ...,
        description="The specific natural language question to ask or the core research query text."
    )
    keywords: List[str] = Field(
        ...,
        description="A list of relevant keywords extracted from or related to the question_text, intended for targeted searching or indexing."
    )

    class Config:
        extra = "forbid"



class Questions(BaseModel):
    satisfied_reason: str = Field(
        ...,
        description="Explain the reasoning behind the 'satisfied' value. If True, state how the provided context allows answering the original user question. If False, explain specifically why the provided context is insufficient to answer the original user question accurately and completely."
    )
    satisfied: bool = Field(
        ...,
        description="Indicates whether the provided context is sufficient to accurately and completely answer the original user question."
    )
    reasoning: str = Field(
        ...,
        description="If 'satisfied' is False, provide a detailed explanation of the information gaps in the current context relative to the original user question. Describe what specific pieces of information are missing and why they are essential to formulate a complete answer based on the context."
    )
    questions: List[Question] = Field(  # <-- Changed from List[str]
        ...,
        description="If 'satisfied' is False, provide a list of structured questions. Each item should contain the specific question ('question_text') and relevant search 'keywords', aimed at acquiring the missing information identified in 'reasoning'." # <-- Updated description
    )