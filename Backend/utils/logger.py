import logging
import sys
import json
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def log_llm_call(
    model: str,
    messages: List[Dict[str, str]],
    response: Optional[Any] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    error: Optional[str] = None,
    function_name: Optional[str] = None
) -> None:
    """
    Log LLM call details to console.
    """
    try:
        log_entry = {
            "function": function_name,
            "model": model,
            "error": error
        }
        
        if error:
            logger.error(f"LLM Call Error: {json.dumps(log_entry)}")
        else:
            # For success, just log a summary to avoid cluttering logs
            if response and hasattr(response, 'usage'):
                log_entry['usage'] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            logger.info(f"LLM Call Success: {json.dumps(log_entry)}")
            
    except Exception as e:
        logger.error(f"Failed to log LLM call: {e}")

def log_mermaid_code(
    mermaid_code: str,
    code_type: str = "mermaid",
    function_name: Optional[str] = None,
    context: Optional[str] = None
) -> None:
    """
    Log generated mermaid code to console.
    """
    try:
        logger.info(f"Mermaid Code ({code_type}) from {function_name}: {len(mermaid_code)} chars")
        # Optional: Log the first few lines if needed for debug
        # logger.info(f"Preview: {mermaid_code[:100]}...")
    except Exception as e:
        logger.error(f"Failed to log mermaid code: {e}")