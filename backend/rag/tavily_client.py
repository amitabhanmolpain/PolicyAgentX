import os
import logging
import hashlib
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# Singleton client instance
_tavily_client = None

# Global cache for search results keyed by (policy_text_hash, query_type)
_search_cache = {}

def get_tavily_client() -> TavilyClient:
    """
    Get or initialize the singleton Tavily client.
    Raises ValueError if TAVILY_API_KEY is missing.
    """
    global _tavily_client
    if _tavily_client is not None:
        return _tavily_client
        
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY environment variable is missing. "
            "Please ensure it is set in your .env file."
        )
    
    _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client

def get_policy_hash(policy_text: str) -> str:
    """
    Generate a stable SHA256 hash for the policy text.
    """
    return hashlib.sha256(policy_text.strip().encode("utf-8")).hexdigest()

def fetch_web_context(
    query: str,
    max_tokens: int = 1500,
    include_domains: list = None,
    exclude_domains: list = None,
    policy_text: str = None,
    query_type: str = None
) -> str:
    """
    Fetch search context from Tavily. Wraps all calls in try/except to avoid crashing the pipeline.
    """
    cache_key = None
    if policy_text is not None and query_type is not None:
        policy_hash = get_policy_hash(policy_text)
        cache_key = (policy_hash, query_type)
        if cache_key in _search_cache:
            logger.info(f"Tavily Cache Hit for query type: {query_type}")
            return _search_cache[cache_key]

    try:
        client = get_tavily_client()
        logger.info(f"Calling Tavily API with query: '{query}'")
        
        context = client.get_search_context(
            query=query,
            max_tokens=max_tokens,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
    except Exception as e:
        logger.error(f"Tavily API call failed for query '{query}': {e}", exc_info=True)
        context = ""
        
    if cache_key is not None:
        _search_cache[cache_key] = context
        
    return context

def get_cached_web_context(policy_text: str, query_type: str) -> str:
    """
    Convenience helper to retrieve or perform a targeted search based on policy text and query type.
    """
    if not policy_text:
        return ""
        
    policy_hash = get_policy_hash(policy_text)
    cache_key = (policy_hash, query_type)
    if cache_key in _search_cache:
        return _search_cache[cache_key]
        
    # Generate query based on the first line / description of the policy
    policy_summary = policy_text.strip().split("\n")[0].strip()
    if len(policy_summary) > 100:
        policy_summary = policy_summary[:100] + "..."
        
    if query_type == "general":
        query = f"Indian policy framework and implementation details: {policy_summary}"
        return fetch_web_context(query, policy_text=policy_text, query_type=query_type)
        
    elif query_type == "government":
        # Government search - biased towards .gov and .gov.in domains
        query = f"Indian government official policy circulars and updates: {policy_summary}"
        gov_domains = ["gov.in", "pib.gov.in", "india.gov.in", "nic.in"]
        return fetch_web_context(
            query,
            include_domains=gov_domains,
            policy_text=policy_text,
            query_type=query_type
        )
        
    elif query_type == "economic":
        query = f"Indian economic stats GDP inflation employment impact: {policy_summary}"
        return fetch_web_context(query, policy_text=policy_text, query_type=query_type)
        
    elif query_type == "news_conflict":
        # News and controversy/unrest search - biased towards news domains
        query = f"Indian public reaction protests unrest controversy: {policy_summary}"
        news_domains = [
            "ndtv.com",
            "thehindu.com",
            "indianexpress.com",
            "timesofindia.indiatimes.com",
            "livemint.com",
            "moneycontrol.com",
            "business-standard.com"
        ]
        return fetch_web_context(
            query,
            include_domains=news_domains,
            policy_text=policy_text,
            query_type=query_type
        )
        
    else:
        logger.warning(f"Unknown query type: {query_type}")
        return ""

def clear_search_cache():
    """
    Clear the in-memory Tavily cache.
    """
    global _search_cache
    _search_cache.clear()
    logger.info("Tavily search cache cleared.")
