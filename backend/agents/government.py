from rag.gemini_client import generate_async
from app.services.gemini_service import response_text


async def government_agent(state: dict, web_context: str = "") -> dict:
    """
    Analyze government-level impacts of policy (fiscal and operational)
    
    Args:
        state: Policy state with policy_text and region
        web_context: Optional Web context from search APIs
    
    Returns:
        Dictionary with government impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1400]
    
    if not web_context:
        web_context = state.get("web_contexts", {}).get("government", "")
    if not web_context:
        try:
            from rag.tavily_client import get_cached_web_context_async
            web_context = await get_cached_web_context_async(policy_text, "government")
        except Exception:
            web_context = ""

    prompt = f"""Answer in 8 words MAXIMUM per line. Be brief.

Policy: {policy_text}

Historical Protest Context (India):
{rag_context}

Government and Policy Web Context (official updates and circulars):
{web_context}

Answer format:
REVENUE_IMPACT:
FISCAL_DEFICIT_IMPACT:
FEASIBILITY:"""

    response = response_text(await generate_async(prompt))
    
    result = {
        "government_analysis": response,
        "revenue_impact": _extract_section(response, "REVENUE_IMPACT"),
        "fiscal_deficit_impact": _extract_section(response, "FISCAL_DEFICIT_IMPACT"),
        "feasibility": _extract_section(response, "FEASIBILITY"),
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
