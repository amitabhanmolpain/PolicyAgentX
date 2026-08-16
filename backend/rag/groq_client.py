import os
import logging
import hashlib
from typing import Dict, Tuple
from groq import Groq

logger = logging.getLogger(__name__)

# Singleton client instance
_groq_client = None

# In-memory cache for Groq completions
# Key is tuple: (prompt_hash, model_name)
_groq_cache: Dict[Tuple[str, str], str] = {}

def get_groq_client() -> Groq:
    """
    Retrieve or initialize the singleton Groq API client.
    First checks GROQ_API_KEY, raises ValueError if missing.
    """
    global _groq_client
    if _groq_client is not None:
        return _groq_client
        
    api_key = os.getenv("GROQ_API_KEY")
        
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is missing. "
            "Please configure it in backend/.env."
        )
        
    _groq_client = Groq(api_key=api_key)
    logger.info("Groq API Client initialized successfully.")
    return _groq_client

def get_prompt_hash(prompt: str) -> str:
    """Generate a stable SHA256 hash for prompt strings."""
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

def generate(
    prompt: str, 
    model: str = "qwen/qwen3.6-27b", 
    temperature: float = None, 
    max_tokens: int = None
) -> str:
    """
    Synchronously generate content from the Groq API with caching.
    """
    import time
    
    prompt_hash = get_prompt_hash(prompt)
    cache_key = (prompt_hash, model)
    
    if cache_key in _groq_cache:
        logger.info(f"Groq Cache Hit for model: {model}")
        return _groq_cache[cache_key]
        
    retries = 4
    delay = 12.0
    
    for attempt in range(retries):
        try:
            client = get_groq_client()
            logger.info(f"Calling Groq API (Sync) with model: {model} (Attempt {attempt+1}/{retries})")
            
            kwargs = {}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
                
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            result = response.choices[0].message.content or ""
            _groq_cache[cache_key] = result
            return result
            
        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code in (400, 401, 403, 404):
                logger.error(f"Groq API call failed with unrecoverable error ({e.status_code}): {e}")
                return ""
            if attempt < retries - 1:
                logger.warning(f"Groq API call failed. Retrying in {delay:.1f}s... (Attempt {attempt+1}/{retries}). Error: {e}")
                time.sleep(delay)
                delay *= 2.0
                continue
            logger.error(f"Groq API call failed: {e}", exc_info=True)
            return ""
            
    return ""

async def generate_async(
    prompt: str, 
    model: str = "qwen/qwen3.6-27b", 
    temperature: float = None, 
    max_tokens: int = None
) -> str:
    """
    Asynchronously generate content from the Groq API with caching.
    Non-blocking, using asyncio.to_thread to run sync generation in background thread.
    """
    import asyncio
    return await asyncio.to_thread(generate, prompt, model, temperature, max_tokens)

def clear_groq_cache():
    """Clear the in-memory Groq response cache."""
    global _groq_cache
    _groq_cache.clear()
    logger.info("Groq response cache cleared.")
