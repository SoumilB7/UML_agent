from pydantic import BaseModel


class DiagramRequest(BaseModel):
    prompt: str


class DiagramEditRequest(BaseModel):
    prompt: str
    existing_mermaid_code: str


class DiagramResponse(BaseModel):
    mermaid_code: str

