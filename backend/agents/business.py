from app.services.gemini_service import generate, response_text


def business_agent(state: dict) -> dict:
    """
    Analyze business impact of policy on Indian industries and commerce
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with business impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1400]
    
    prompt = f"""Answer in 8 words MAXIMUM per line. No explanations.

Policy: {policy_text}

Historical Protest Context (India):
{rag_context}

Answer format:
SMALL_BUSINESS_IMPACT:
LARGE_INDUSTRY_IMPACT:
SUPPLY_CHAIN_IMPACT:"""

    response = response_text(generate(prompt))
    
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
    except:
        return ""
