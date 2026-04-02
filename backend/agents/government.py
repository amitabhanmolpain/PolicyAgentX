from app.services.gemini_service import generate, response_text


def government_agent(state: dict) -> dict:
    """
    Analyze government-level impacts of policy (fiscal and operational)
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with government impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    
    prompt = f"""Answer in 8 words MAXIMUM per line. Be brief.

Policy: {policy_text}

Answer format:
REVENUE_IMPACT:
FISCAL_DEFICIT_IMPACT:
FEASIBILITY:"""

    response = response_text(generate(prompt))
    
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
    except:
        return ""
