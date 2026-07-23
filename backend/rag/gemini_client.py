import os
import logging
import hashlib
from typing import Dict, Tuple
from google import genai

logger = logging.getLogger(__name__)

# Singleton client instance
_gemini_client = None

# In-memory cache for Gemini completions
# Key is tuple: (prompt_hash, model_name)
# NOTE: In multi-worker production environments, this should be moved to Redis or MongoDB.
_gemini_cache: Dict[Tuple[str, str], str] = {}

def get_gemini_client() -> genai.Client:
    """
    Retrieve or initialize the singleton Gemini Developer API client.
    First checks GEMINI_API_KEY, falls back to GOOGLE_API_KEY, raises ValueError if both missing.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback to GOOGLE_API_KEY if GEMINI_API_KEY is not directly set
        api_key = os.getenv("GOOGLE_API_KEY")
        
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is missing. "
            "Please configure it in backend/.env."
        )
        
    _gemini_client = genai.Client(api_key=api_key)
    logger.info("Gemini Developer API Client initialized successfully.")
    return _gemini_client

def get_prompt_hash(prompt: str) -> str:
    """Generate a stable SHA256 hash for prompt strings."""
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

def generate(
    prompt: str, 
    model: str = "gemini-2.5-flash", 
    temperature: float = None, 
    max_tokens: int = None
) -> str:
    """
    Synchronously generate content from the Gemini API with caching and 429 retries.
    """
    import time
    from google.genai.errors import APIError
    
    prompt_hash = get_prompt_hash(prompt)
    cache_key = (prompt_hash, model)
    
    if cache_key in _gemini_cache:
        logger.info(f"Gemini Cache Hit for model: {model}")
        return _gemini_cache[cache_key]
        
    retries = 3
    delay = 12.0  # Wait slightly longer than standard 11s free tier limit window
    
    for attempt in range(retries):
        try:
            client = get_gemini_client()
            logger.info(f"Calling Gemini API (Sync) with model: {model} (Attempt {attempt+1}/{retries})")
            
            config = {}
            if temperature is not None:
                config["temperature"] = temperature
            if max_tokens is not None:
                config["max_output_tokens"] = max_tokens
                
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config if config else None
            )
            result = response.text or ""
            _gemini_cache[cache_key] = result
            return result
            
        except APIError as e:
            # Catch 429 / Resource Exhausted rate limit errors
            is_rate_limit = getattr(e, "code", None) == 429 or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_rate_limit and attempt < retries - 1:
                logger.warning(f"Gemini rate limit hit. Retrying in {delay:.1f}s... (Attempt {attempt+1}/{retries})")
                time.sleep(delay)
                delay *= 2.0
                continue
            logger.error(f"Gemini API call failed with API error: {e}", exc_info=True)
            return ""
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}", exc_info=True)
            return ""
            
    return ""

async def generate_async(
    prompt: str, 
    model: str = "gemini-2.5-flash", 
    temperature: float = None, 
    max_tokens: int = None
) -> str:
    """
    Asynchronously generate content from the Gemini API with caching.
    Non-blocking, using asyncio.to_thread to run sync generation in background thread.
    """
    import asyncio
    return await asyncio.to_thread(generate, prompt, model, temperature, max_tokens)

def clear_gemini_cache():
    """Clear the in-memory Gemini response cache."""
    global _gemini_cache
    _gemini_cache.clear()
    logger.info("Gemini response cache cleared.")
