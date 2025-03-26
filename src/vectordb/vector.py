from dataclasses import dataclass
from typing import List, Optional


from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Vector:
    """
    A class to represent a vector in a vector storage.
    """
    vector: List[float]
    file_name: str
    file_position: int
    content: str
    metadata: dict
    id: Optional[int] = None
    updated_at: Optional[str] = None


