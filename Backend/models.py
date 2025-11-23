from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DiagramRequest(BaseModel):
    prompt: str
    num_variations: Optional[int] = 1  


class DiagramEditRequest(BaseModel):
    prompt: str
    existing_mermaid_code: str


class DiagramResponse(BaseModel):
    mermaid_code: str
    variations: Optional[List[str]] = None 


# RL Action Models
class RLActionRequest(BaseModel):
    action_type: str  
    timestamp: Optional[str] = None
    metadata: Optional[dict] = None
    
    # User tracking fields
    user_id: str
    session_id: str

    rating: Optional[int] = None
    feedback_text: Optional[str] = None

    prompt: Optional[str] = None
    previous_prompt: Optional[str] = None

    variation_index: Optional[int] = None
    all_variations: Optional[List[str]] = None

    mermaid_code: Optional[str] = None
    diagram_id: Optional[str] = None


class RLActionResponse(BaseModel):
    success: bool
    message: str
    action_id: Optional[str] = None
