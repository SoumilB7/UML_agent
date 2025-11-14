import logging
from fastapi import APIRouter, HTTPException

from models import DiagramRequest, DiagramEditRequest, DiagramResponse
from utils.diagram import generate_diagram_mermaid
from utils.editor import edit_diagram_mermaid


router = APIRouter(prefix="/diagram", tags=['diagram'])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=DiagramResponse)
async def generate_diagram(request: DiagramRequest):
    """
    Generate Mermaid UML diagram code from a user prompt.
    
    Args:
        request: DiagramRequest containing the user's prompt and num_variations
        
    Returns:
        DiagramResponse containing the Mermaid code(s)
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    num_variations = request.num_variations or 1
    if num_variations < 1:
        num_variations = 1
    if num_variations > 3:
        num_variations = 3  # Limit to 3 variations max
    
    try:
        if num_variations == 1:
            # Single generation
            mermaid_code = generate_diagram_mermaid(request.prompt)
            return DiagramResponse(mermaid_code=mermaid_code)
        else:
            # Multiple variations
            variations = []
            for i in range(num_variations):
                logger.info(f"Generating variation {i+1}/{num_variations}")
                variation = generate_diagram_mermaid(request.prompt)
                variations.append(variation)
            
            # Return first variation as mermaid_code for backward compatibility
            # and all variations in the variations list
            return DiagramResponse(
                mermaid_code=variations[0],
                variations=variations
            )
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in generate_diagram endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate diagram")


@router.post("/edit", response_model=DiagramResponse)
async def edit_diagram(request: DiagramEditRequest):
    """
    Edit/update existing Mermaid UML diagram code based on a user prompt.
    
    Args:
        request: DiagramEditRequest containing the user's edit prompt and existing mermaid code
        
    Returns:
        DiagramResponse containing the updated Mermaid code
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    if not request.existing_mermaid_code or not request.existing_mermaid_code.strip():
        raise HTTPException(status_code=400, detail="Existing mermaid code cannot be empty")
    
    try:
        updated_mermaid_code = edit_diagram_mermaid(
            user_prompt=request.prompt,
            existing_mermaid_code=request.existing_mermaid_code
        )
        return DiagramResponse(mermaid_code=updated_mermaid_code)
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in edit_diagram endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to edit diagram")
