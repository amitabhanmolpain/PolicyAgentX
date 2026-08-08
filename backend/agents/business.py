from rag.groq_client import generate_async
from app.services.groq_service import response_text


async def business_agent(state: dict, web_context: str = "") -> dict:
    """
    Analyze business impact of policy on Indian industries and commerce
    
    Args:
        state: Policy state with policy_text and region
        web_context: Optional Web context from search APIs
    
    Returns:
        Dictionary with business impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1400]
    
    if not web_context:
        web_context = state.get("web_contexts", {}).get("general", "")
    if not web_context:
        try:
            from rag.tavily_client import get_cached_web_context_async
            web_context = await get_cached_web_context_async(policy_text, "general")
        except Exception:
            web_context = ""

    prompt = f"""Answer in 8 words MAXIMUM per line. No explanations.

Policy: {policy_text}

Historical Protest Context (India):
{rag_context}

Business and Commerce Web Context:
{web_context}

Answer format:
SMALL_BUSINESS_IMPACT:
LARGE_INDUSTRY_IMPACT:
SUPPLY_CHAIN_IMPACT:"""

    response = response_text(await generate_async(prompt))
    
    result = {
        "business_analysis": response,
        "small_business_impact": _extract_section(response, "SMALL_BUSINESS_IMPACT"),
        "large_industry_impact": _extract_section(response, "LARGE_INDUSTRY_IMPACT"),
        "supply_chain_impact": _extract_section(response, "SUPPLY_CHAIN_IMPACT"),
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
