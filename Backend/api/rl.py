import logging
import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List
import uuid

from models import RLActionRequest, RLActionResponse

router = APIRouter(prefix="/rl", tags=['rl'])
logger = logging.getLogger(__name__)

# Path to store RL actions JSON file
RL_ACTIONS_FILE = Path(__file__).parent.parent.parent / "rl_actions.json"


def ensure_rl_actions_file():
    """Ensure the RL actions JSON file exists, create if it doesn't"""
    if not RL_ACTIONS_FILE.exists():
        with open(RL_ACTIONS_FILE, 'w') as f:
            json.dump([], f)
        logger.info(f"Created RL actions file at {RL_ACTIONS_FILE}")


def load_rl_actions() -> List[dict]:
    """Load all RL actions from the JSON file"""
    ensure_rl_actions_file()
    try:
        with open(RL_ACTIONS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_rl_action(action_data: dict):
    """Save a single RL action to the JSON file"""
    ensure_rl_actions_file()
    actions = load_rl_actions()
    
    # Add action to the list
    actions.append(action_data)
    
    # Write back to file
    try:
        with open(RL_ACTIONS_FILE, 'w') as f:
            json.dump(actions, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved RL action: {action_data.get('action_type')}")
    except Exception as e:
        logger.error(f"Failed to save RL action: {e}", exc_info=True)
        raise


@router.post("/action", response_model=RLActionResponse)
async def record_rl_action(request: RLActionRequest):
    """
    Record a user action for RL training purposes.
    
    Args:
        request: RLActionRequest containing action details
        
    Returns:
        RLActionResponse confirming the action was recorded
    """
    try:
        # Generate action ID
        action_id = str(uuid.uuid4())
        
        # Prepare action data
        action_data = {
            "action_id": action_id,
            "action_type": request.action_type,
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            "metadata": request.metadata or {},
        }
        
        # Add optional fields if present
        if request.rating is not None:
            action_data["rating"] = request.rating
        
        if request.feedback_text:
            action_data["feedback_text"] = request.feedback_text
        
        if request.prompt:
            action_data["prompt"] = request.prompt
        
        if request.previous_prompt:
            action_data["previous_prompt"] = request.previous_prompt
        
        if request.variation_index is not None:
            action_data["variation_index"] = request.variation_index
        
        if request.all_variations:
            action_data["all_variations"] = request.all_variations
        
        if request.mermaid_code:
            action_data["mermaid_code"] = request.mermaid_code
        
        if request.diagram_id:
            action_data["diagram_id"] = request.diagram_id
        
        # Save to JSON file
        save_rl_action(action_data)
        
        return RLActionResponse(
            success=True,
            message=f"Action '{request.action_type}' recorded successfully",
            action_id=action_id
        )
    
    except Exception as e:
        logger.error(f"Error recording RL action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record action: {str(e)}")


@router.get("/actions")
async def get_rl_actions():
    """
    Get all recorded RL actions (for debugging/admin purposes).
    
    Returns:
        List of all recorded actions
    """
    try:
        actions = load_rl_actions()
        return {"actions": actions, "count": len(actions)}
    except Exception as e:
        logger.error(f"Error loading RL actions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load actions: {str(e)}")

