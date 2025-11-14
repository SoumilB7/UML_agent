import json
import logging
import re
import base64
from typing import Optional
import dotenv
import httpx

from constants import OPENAI_MODEL_NAME, MERMAID_SYSTEM_PROMPT
from openai import OpenAI
from utils.logger import log_llm_call


OPANAI_API_KEY = dotenv.get_key('.env', 'OPENAI_API_KEY')  # Ensure .env is loaded
logger = logging.getLogger(__name__)


def get_openai_client():
    """
    Returns an OpenAI client instance.
    """
    api_key = OPANAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")
    return OpenAI(api_key=api_key)


def extract_mermaid_code(text: str) -> str:
    """
    Extracts Mermaid code from the model's response.
    Handles cases where the model wraps code in markdown code blocks.
    
    Args:
        text (str): The raw response from the model.
        
    Returns:
        str: The extracted Mermaid code.
    """
    # Remove markdown code blocks if present
    text = text.strip()
    
    # Check for ```mermaid or ``` blocks
    mermaid_pattern = r'```(?:mermaid)?\s*(.*?)```'
    match = re.search(mermaid_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no code blocks, return the text as-is (assuming it's already Mermaid code)
    return text


def unescape_mermaid_code(mermaid_code: str) -> str:
    """
    Unescapes escape sequences in Mermaid code to make it renderable.
    Converts escape sequences like \\n to actual newlines, \\" to quotes, etc.
    
    This function handles cases where the model returns strings with literal
    escape sequences (like "\\n" as two characters) that need to be converted
    to their actual character equivalents (like a real newline).
    
    Args:
        mermaid_code (str): The Mermaid code with potential escape sequences
        
    Returns:
        str: The unescaped Mermaid code ready for rendering
    """
    try:
        # First, check if it's a JSON-encoded string (starts and ends with quotes)
        if mermaid_code.startswith('"') and mermaid_code.endswith('"'):
            try:
                # If it's a JSON-encoded string, decode it first
                # This handles cases where the entire string is JSON-encoded
                mermaid_code = json.loads(mermaid_code)
            except json.JSONDecodeError:
                # If JSON decode fails, continue with original string
                pass
        
        # Now handle escape sequences
        # The model might return strings with literal backslash sequences like "\\n"
        # We need to convert these to actual characters
        
        # Use Python's codecs.decode with 'unicode_escape' to handle escape sequences
        # This is the most reliable way to convert \n, \t, \", etc. to their actual characters
        # We encode to bytes using 'raw_unicode_escape' first to preserve the escape sequences
        # as they are, then decode with 'unicode_escape' to interpret them
        
        try:
            # Method 1: Use encode/decode to properly handle escape sequences
            # Encode to bytes, then decode with unicode_escape to convert \n to newline
            # This converts literal \n (backslash+n) to actual newline character
            unescaped = mermaid_code.encode('utf-8').decode('unicode_escape')
        except (UnicodeDecodeError, ValueError, UnicodeEncodeError):
            # Method 2: If codecs fails, do manual replacement
            # This handles the case where escape sequences are literal strings
            unescaped = mermaid_code
            # Replace in order: handle \\ first to avoid double replacement issues
            # Then handle other escape sequences
            escape_replacements = [
                ('\\\\', '\x00BACKSLASH\x00'),  # Temporary placeholder for backslashes
                ('\\n', '\n'),   # Newline
                ('\\t', '\t'),   # Tab
                ('\\r', '\r'),   # Carriage return
                ('\\"', '"'),    # Double quote
                ("\\'", "'"),    # Single quote
                ('\x00BACKSLASH\x00', '\\'),  # Restore backslashes
            ]
            
            for old, new in escape_replacements:
                unescaped = unescaped.replace(old, new)
        
        return unescaped
    except Exception as e:
        logger.warning(f"Error unescaping Mermaid code, using original: {e}")
        # If unescaping fails, return original (might already be properly formatted)
        return mermaid_code


def render_mermaid_to_image(mermaid_code: str, format: str = "png") -> Optional[bytes]:
    """
    Renders Mermaid code to an image using mermaid.ink API.
    
    Args:
        mermaid_code (str): The Mermaid diagram code (may contain escape sequences)
        format (str): Image format - 'png' or 'svg' (default: 'png')
        
    Returns:
        bytes: Image data as bytes, or None if rendering fails
    """
    try:
        # First, unescape the Mermaid code to convert \n to newlines, \" to quotes, etc.
        cleaned_code = unescape_mermaid_code(mermaid_code)
        logger.debug(f"Cleaned Mermaid code (first 200 chars): {cleaned_code[:200]}")
        
        # Encode the cleaned Mermaid code to base64url (URL-safe base64)
        mermaid_base64 = base64.urlsafe_b64encode(cleaned_code.encode('utf-8')).decode('utf-8')
        # Remove padding if present (mermaid.ink doesn't need it)
        mermaid_base64 = mermaid_base64.rstrip('=')
        
        # Use mermaid.ink API to render the diagram
        # For PNG: /img/{base64}, For SVG: /svg/{base64}
        endpoint = "svg" if format.lower() == "svg" else "img"
        url = f"https://mermaid.ink/{endpoint}/{mermaid_base64}"
        
        logger.info(f"Rendering Mermaid diagram to {format} via mermaid.ink")
        logger.debug(f"Request URL (first 100 chars): {url[:100]}...")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            # Check if we got an image response
            content_type = response.headers.get('content-type', '')
            logger.debug(f"Content type: {content_type}")
            
            if content_type.startswith('image/') or content_type == 'image/svg+xml':
                image_size = len(response.content)
                logger.info(f"Successfully rendered image, size: {image_size} bytes")
                return response.content
            else:
                response_text = response.text[:500] if hasattr(response, 'text') else str(response.content[:500])
                logger.error(f"Unexpected content type: {content_type}")
                logger.error(f"Response body: {response_text}")
                return None
                
    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if hasattr(e.response, 'text') else str(e.response.content[:500])
        logger.error(f"HTTP error rendering Mermaid diagram: {e.response.status_code}")
        logger.error(f"Error response: {error_text}")
        logger.error(f"Request URL was: {url if 'url' in locals() else 'N/A'}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error rendering Mermaid diagram: {e}")
        return None
    except Exception as e:
        logger.error(f"Error rendering Mermaid diagram: {e}", exc_info=True)
        return None


def generate_diagram_mermaid(user_prompt: str) -> str:
    """
    Calls OpenAI API to generate a Mermaid UML diagram code for the user's prompt.

    Args:
        user_prompt (str): The user's prompt describing the UML diagram they want.

    Returns:
        str: The Mermaid code for the UML diagram, or None if an error occurs.
    """
    try:
        openai_client = get_openai_client()
        
        system_prompt = MERMAID_SYSTEM_PROMPT

        logger.info(f"Generating Mermaid UML diagram for prompt: {user_prompt[:100]}...")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=messages,
            temperature=0.3,
            top_p=0.7,
            stream=False,
        )

        # Log the LLM call
        log_llm_call(
            model=OPENAI_MODEL_NAME,
            messages=messages,
            response=response,
            temperature=0.3,
            top_p=0.7,
            function_name="generate_diagram_mermaid"
        )

        raw_answer = response.choices[0].message.content.strip()
        
        # Extract Mermaid code (in case model wraps it in markdown)
        mermaid_code = extract_mermaid_code(raw_answer)
        
        logger.info(f"Generated Mermaid code (length: {len(mermaid_code)} chars)")
        return mermaid_code

    except Exception as e:
        # Log the error
        log_llm_call(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": MERMAID_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            top_p=0.7,
            error=str(e),
            function_name="generate_diagram_mermaid"
        )
        logger.error(f"Error while generating Mermaid diagram: {e}", exc_info=True)
        raise



