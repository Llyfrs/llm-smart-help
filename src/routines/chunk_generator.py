from typing import Literal
from blib2to3.pgen2.tokenize import Callable


def chunk_generator(chunk_size: int, chunking_strategy: Literal["max_tokens", "balanced", "min_tokens"] = "balanced", tokenizer: Callable[[str], list[int]] = None):

    pass