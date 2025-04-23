from typing import List

from pydantic import BaseModel
from pydantic.fields import Field


class Questions(BaseModel):
    reasoning: str = Field(
        ..., description="Reason about the question you will ask. What information you will need and why. "
    )
    questions: List[str] = Field(..., description="List of terms that need clarification")
