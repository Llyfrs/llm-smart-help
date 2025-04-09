from typing import List

from pydantic import BaseModel
from pydantic.fields import Field


class Terms(BaseModel):
    reasoning: str = Field(
        ..., description="Reasoning behind the need for clarification"
    )
    terms: List[str] = Field(..., description="List of terms that need clarification")
