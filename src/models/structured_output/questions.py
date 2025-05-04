from pydantic import BaseModel, Field
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
        description="Assess whether the given context provides enough information to fully and confidently answer the original user question. "
                    "Reference the specific components of the question and analyze whether each one is addressed directly and completely by the context. "
                    "Indicate if any terms or criteria from the question are used without clear, contextually appropriate definitions or explanations. "
                    "If any assumptions, ambiguities, or missing pieces would require clarification or external verification, explain what they are and how they impact the completeness or reliability of the answer. "
                    "Conclude clearly whether the context is sufficient, and justify that conclusion based on your analysis."
    )
    satisfied: bool = Field(
        ...,
        description="Indicates whether the provided context is sufficient to accurately and completely answer the original user question."
    )
    reasoning: str = Field(
        ...,
        description="Review satisfied_reason to identify any missing or unclear information, especially undefined terms from the original_user_question. "
                    "For each gap, explain why it matters—what analysis or conclusion can't be made without it. "
                    "Then reflect on how the reasoning could improve: Were assumptions made too quickly? "
                    "Could a different interpretation of the question have helped? "
                    "Suggest how the next question could be better phrased or targeted to fill these gaps, using the context already available."
    )
    questions: List[Question] = Field(  # <-- Changed from List[str]
        ...,
        description="If 'satisfied' is False, provide a list of structured questions. Each item should contain the specific question ('question_text') and relevant search 'keywords', aimed at acquiring the missing information identified in 'reasoning'." # <-- Updated description
    )