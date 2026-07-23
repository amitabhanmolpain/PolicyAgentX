from app.services.gemini_service import generate, response_text


def economic_agent(state: dict, web_context: str = "") -> dict:
    """
    Analyze economic impact of policy on India
    
    Args:
        state: Policy state with policy_text and region
        web_context: Optional Web context from search APIs
    
    Returns:
        Dictionary with economic analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1400]
    
    if not web_context:
        web_context = state.get("web_contexts", {}).get("economic", "")
    if not web_context:
        try:
            from rag.tavily_client import get_cached_web_context
            web_context = get_cached_web_context(policy_text, "economic")
        except Exception:
            web_context = ""

    prompt = f"""Answer in 8 words MAXIMUM per line. No long answers.

Policy: {policy_text}

Historical Protest Context (India):
{rag_context}

Current Economic Statistics & Context (Tavily):
{web_context}

Answer format:
GDP_IMPACT:
INFLATION_IMPACT:
EMPLOYMENT_IMPACT:"""

    response = response_text(generate(prompt))
    
    result = {
        "economic_analysis": response,
        "gdp_impact": _extract_section(response, "GDP_IMPACT"),
        "inflation_impact": _extract_section(response, "INFLATION_IMPACT"),
        "employment_impact": _extract_section(response, "EMPLOYMENT_IMPACT"),
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
    except:
        return ""
