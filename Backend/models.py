from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DiagramRequest(BaseModel):
    prompt: str
    num_variations: Optional[int] = 1  # Number of variations to generate (1 for single, 3 for many)


class DiagramEditRequest(BaseModel):
    prompt: str
    existing_mermaid_code: str


class DiagramResponse(BaseModel):
    mermaid_code: str
    variations: Optional[List[str]] = None  # List of mermaid codes when multiple variations are generated


# RL Action Models
class RLActionRequest(BaseModel):
    action_type: str  # e.g., "image_copy", "variation_selection", "variation_hover", "tab_away", "new_button", "mermaid_copy", "prompt_update", "feedback"
    timestamp: Optional[str] = None  # ISO format timestamp
    metadata: Optional[dict] = None  # Additional context about the action
    # For feedback actions
    rating: Optional[int] = None  # 1-5 star rating
    feedback_text: Optional[str] = None  # Text feedback
    # For prompt updates
    prompt: Optional[str] = None  # Updated prompt text
    previous_prompt: Optional[str] = None  # Previous prompt for comparison
    # For variation selection
    variation_index: Optional[int] = None  # Which variation was selected
    all_variations: Optional[List[str]] = None  # All variation codes (all 3 versions)
    # For diagram context
    mermaid_code: Optional[str] = None  # Current mermaid code (selected variation for variation_selection)
    diagram_id: Optional[str] = None  # Unique identifier for the diagram session


class RLActionResponse(BaseModel):
    success: bool
    message: str
    action_id: Optional[str] = None
