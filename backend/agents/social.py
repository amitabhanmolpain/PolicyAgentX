from rag.gemini_client import generate_async
from app.services.gemini_service import response_text


async def social_agent(state: dict, web_context: str = "") -> dict:
    """
    Analyze social impact of policy on different Indian population segments
    
    Args:
        state: Policy state with policy_text and region
        web_context: Optional Web context from search APIs
    
    Returns:
        Dictionary with social impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1400]
    
    if not web_context:
        web_context = state.get("web_contexts", {}).get("news_conflict", "")
    if not web_context:
        try:
            from rag.tavily_client import get_cached_web_context_async
            web_context = await get_cached_web_context_async(policy_text, "news_conflict")
        except Exception:
            web_context = ""

    prompt = f"""Answer in 8 words MAXIMUM per line. Use simple words.

Policy: {policy_text}

Historical Protest Context (India):
{rag_context}

Current News & Public Unrest Context (Tavily):
{web_context}

Answer format:
MIDDLE_CLASS_IMPACT:
LOWER_INCOME_IMPACT:
LIFESTYLE_CHANGES:"""

    response = response_text(await generate_async(prompt))
    
    result = {
        "social_analysis": response,
        "middle_class_impact": _extract_section(response, "MIDDLE_CLASS_IMPACT"),
        "lower_income_impact": _extract_section(response, "LOWER_INCOME_IMPACT"),
        "lifestyle_changes": _extract_section(response, "LIFESTYLE_CHANGES"),
    }
    
    return result


def _extract_section(text: str, section: str) -> str:
    """Extract a section from response text"""
    try:
        start = text.find(f"{section}:")
        if start == -1:
            return ""
        start += len(f"{section}:") + 1
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        return text[start:end].strip()
    except Exception:
        return ""
