from typing import List

from pydantic import BaseModel
from pydantic.fields import Field


class Terms(BaseModel):
    reasoning: str = Field(
        ..., description="Reasoning behind the need for clarification. Make sure this is string safe"
    )
    terms: List[str] = Field(..., description="List of terms that need clarification")
