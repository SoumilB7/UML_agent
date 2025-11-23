import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from models import RLActionRequest, RLActionResponse
from utils.database import get_database

router = APIRouter(prefix="/rl", tags=['rl'])
logger = logging.getLogger(__name__)


@router.post("/action", response_model=RLActionResponse)
async def record_rl_action(
    request: RLActionRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Record a user action for RL training purposes into MongoDB.
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
        optional_fields = [
            "rating", "feedback_text", "prompt", "previous_prompt",
            "variation_index", "all_variations", "mermaid_code", "diagram_id"
        ]
        
        for field in optional_fields:
            val = getattr(request, field, None)
            if val is not None:
                action_data[field] = val
        
        # Database operations
        users_collection = db["users"]
        
        # 1. Try to push action to the specific session of the user
        result = await users_collection.update_one(
            {
                "_id": request.user_id,
                "sessions.session_id": request.session_id
            },
            {
                "$push": {"sessions.$.actions": action_data},
                "$set": {"last_active": datetime.utcnow().isoformat()}
            }
        )
        
        # 2. If user or session not found (result.modified_count == 0)
        if result.modified_count == 0:
            # Check if user exists
            user = await users_collection.find_one({"_id": request.user_id})
            
            if user:
                # User exists, but session doesn't -> Create new session with the action
                new_session = {
                    "session_id": request.session_id,
                    "start_time": datetime.utcnow().isoformat(),
                    "actions": [action_data]
                }
                await users_collection.update_one(
                    {"_id": request.user_id},
                    {
                        "$push": {"sessions": new_session},
                        "$set": {"last_active": datetime.utcnow().isoformat()}
                    }
                )
            else:
                # User doesn't exist -> Create new user with session and action
                new_user_doc = {
                    "_id": request.user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_active": datetime.utcnow().isoformat(),
                    "sessions": [
                        {
                            "session_id": request.session_id,
                            "start_time": datetime.utcnow().isoformat(),
                            "actions": [action_data]
                        }
                    ]
                }
                await users_collection.insert_one(new_user_doc)
                logger.info(f"Created new user document for {request.user_id}")

        logger.info(f"Recorded RL action: {request.action_type} for user {request.user_id}")
        
        return RLActionResponse(
            success=True,
            message=f"Action '{request.action_type}' recorded successfully",
            action_id=action_id
        )
    
    except Exception as e:
        logger.error(f"Error recording RL action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record action: {str(e)}")


@router.get("/actions")
async def get_rl_actions(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Get all recorded RL actions (for debugging/admin purposes).
    Returns a flattened list of actions for compatibility.
    """
    try:
        users_collection = db["users"]
        cursor = users_collection.find({})
        users = await cursor.to_list(length=100)
        
        all_actions = []
        for user in users:
            user_id = user["_id"]
            for session in user.get("sessions", []):
                session_id = session.get("session_id")
                for action in session.get("actions", []):
                    # Enrich action with context
                    action["user_id"] = user_id
                    action["session_id"] = session_id
                    all_actions.append(action)
                    
        return {"actions": all_actions, "count": len(all_actions)}
    except Exception as e:
        logger.error(f"Error loading RL actions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load actions: {str(e)}")

