from pydantic import BaseModel
from typing import List, Optional


class DiagramRequest(BaseModel):
    prompt: str
    num_variations: Optional[int] = 1  # Number of variations to generate (1 for single, 3 for many)


class DiagramEditRequest(BaseModel):
    prompt: str
    existing_mermaid_code: str


class DiagramResponse(BaseModel):
    mermaid_code: str
    variations: Optional[List[str]] = None  # List of mermaid codes when multiple variations are generated

