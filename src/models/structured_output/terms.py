from typing import List

from pydantic import BaseModel
from pydantic.fields import Field


class Terms(BaseModel):
    """
    Represents reasoning structure for evaluating the sufficiency of context in answering a user question and allowing for follow-up questions.
    """
    reasoning: str = Field(
        ..., description="Reasoning behind the need for clarification. Make sure this is string safe"
    )
    terms: List[str] = Field(..., description="List of terms that need clarification")
