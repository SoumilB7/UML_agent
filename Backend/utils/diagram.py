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


def get_openai_client(api_key: str = None):
    """
    Returns an OpenAI client instance.
    Args:
        api_key: Optional API key. If not provided, tries to load from .env
    """
    if not api_key:
        api_key = OPANAI_API_KEY
    
    if not api_key:
        raise ValueError("OpenAI API key not found. Please provide it in settings or .env file")
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

    text = text.strip()
    mermaid_pattern = r'```(?:mermaid)?\s*(.*?)```'
    match = re.search(mermaid_pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
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
        if mermaid_code.startswith('"') and mermaid_code.endswith('"'):
            try:
                # If it's a JSON-encoded string, decode it first
                # This handles cases where the entire string is JSON-encoded
                mermaid_code = json.loads(mermaid_code)
            except json.JSONDecodeError:
                # If JSON decode fails, continue with original string
                pass
        

        try:
            unescaped = mermaid_code.encode('utf-8').decode('unicode_escape')
        except (UnicodeDecodeError, ValueError, UnicodeEncodeError):
            unescaped = mermaid_code
            escape_replacements = [
                ('\\\\', '\x00BACKSLASH\x00'),
                ('\\n', '\n'),
                ('\\t', '\t'),
                ('\\r', '\r'),
                ('\\"', '"'),
                ("\\'", "'"),
                ('\x00BACKSLASH\x00', '\\'),
            ]
            
            for old, new in escape_replacements:
                unescaped = unescaped.replace(old, new)
        
        return unescaped
    except Exception as e:
        logger.warning(f"Error unescaping Mermaid code, using original: {e}")
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
        cleaned_code = unescape_mermaid_code(mermaid_code)
        logger.debug(f"Cleaned Mermaid code (first 200 chars): {cleaned_code[:200]}")
        
        mermaid_base64 = base64.urlsafe_b64encode(cleaned_code.encode('utf-8')).decode('utf-8')
        mermaid_base64 = mermaid_base64.rstrip('=')
        
        endpoint = "svg" if format.lower() == "svg" else "img"
        url = f"https://mermaid.ink/{endpoint}/{mermaid_base64}"
        
        logger.info(f"Rendering Mermaid diagram to {format} via mermaid.ink")
        logger.debug(f"Request URL (first 100 chars): {url[:100]}...")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
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


def generate_diagram_mermaid(user_prompt: str, api_key: str = None) -> str:
    """
    Calls OpenAI API to generate a Mermaid UML diagram code for the user's prompt.

    Args:
        user_prompt (str): The user's prompt describing the UML diagram they want.
        api_key (str): Optional OpenAI API key.

    Returns:
        str: The Mermaid code for the UML diagram, or None if an error occurs.
    """
    try:
        openai_client = get_openai_client(api_key)
        
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

        log_llm_call(
            model=OPENAI_MODEL_NAME,
            messages=messages,
            response=response,
            temperature=0.3,
            top_p=0.7,
            function_name="generate_diagram_mermaid"
        )

        raw_answer = response.choices[0].message.content.strip()
        
        mermaid_code = extract_mermaid_code(raw_answer)
        
        logger.info(f"Generated Mermaid code (length: {len(mermaid_code)} chars)")
        return mermaid_code

    except Exception as e:
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



