import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


def _get_log_file_path() -> str:
    """
    Returns the absolute path to the log.txt file in the project root.
    """
    # Get the directory where this logger.py file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to Backend directory
    backend_dir = os.path.dirname(current_dir)
    # Go up to project root
    project_root = os.path.dirname(backend_dir)
    # Create log.txt in project root
    log_file = os.path.join(project_root, "log.txt")
    return log_file


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
    Logs LLM API calls (inputs and outputs) to a log.txt file.
    
    Args:
        model: The model name used for the LLM call
        messages: List of message dictionaries with 'role' and 'content' keys
        response: The response object from the LLM API (optional)
        temperature: Temperature parameter used (optional)
        top_p: Top-p parameter used (optional)
        error: Error message if the call failed (optional)
        function_name: Name of the function making the call (optional)
    """
    log_file = _get_log_file_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "function": function_name or "unknown",
        "model": model,
        "parameters": {
            "temperature": temperature,
            "top_p": top_p
        },
        "input": {
            "messages": messages
        },
        "output": None,
        "error": None
    }
    
    # Add response if available
    if response is not None:
        try:
            # Extract response content
            if hasattr(response, 'choices') and len(response.choices) > 0:
                response_content = response.choices[0].message.content if hasattr(response.choices[0].message, 'content') else str(response.choices[0].message)
                log_entry["output"] = {
                    "content": response_content,
                    "finish_reason": response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else None,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'prompt_tokens') else None,
                        "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens') else None,
                        "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens') else None
                    }
                }
            else:
                log_entry["output"] = {"raw_response": str(response)}
        except Exception as e:
            log_entry["output"] = {"error_extracting_response": str(e), "raw_response": str(response)}
    
    # Add error if available
    if error is not None:
        log_entry["error"] = error
    
    # Format log entry as readable text
    log_text = f"""
{'='*80}
LLM Call Log Entry
{'='*80}
Timestamp: {log_entry['timestamp']}
Function: {log_entry['function']}
Model: {log_entry['model']}
Parameters: {json.dumps(log_entry['parameters'], indent=2)}

Input Messages:
{'-'*80}
"""
    
    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        # Truncate very long content for readability (show first 500 chars)
        content_preview = content[:500] + "..." if len(content) > 500 else content
        log_text += f"Message {i} ({role}):\n{content_preview}\n\n"
    
    log_text += f"{'-'*80}\n"
    
    if log_entry['output']:
        log_text += "Output:\n"
        log_text += f"{'-'*80}\n"
        if 'content' in log_entry['output']:
            output_content = log_entry['output']['content']
            # Truncate very long output for readability (show first 1000 chars)
            output_preview = output_content[:1000] + "..." if len(output_content) > 1000 else output_content
            log_text += f"Content:\n{output_preview}\n\n"
        
        if 'usage' in log_entry['output'] and log_entry['output']['usage']:
            usage = log_entry['output']['usage']
            log_text += f"Token Usage:\n"
            log_text += f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}\n"
            log_text += f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}\n"
            log_text += f"  Total tokens: {usage.get('total_tokens', 'N/A')}\n\n"
        
        if 'finish_reason' in log_entry['output']:
            log_text += f"Finish reason: {log_entry['output']['finish_reason']}\n"
    
    if log_entry['error']:
        log_text += f"\nError:\n{'-'*80}\n{log_entry['error']}\n"
    
    log_text += f"\n{'='*80}\n\n"
    
    # Append to log file
    try:
        # Ensure the directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Ensure the log file exists and append to it
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_text)
    except Exception as e:
        # If logging fails, at least print to console
        print(f"Warning: Failed to write to log file at {log_file}: {e}")
        print(f"Attempted log content:\n{log_text}")
