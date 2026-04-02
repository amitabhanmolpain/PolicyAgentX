from app.services.gemini_service import generate, response_text


def social_agent(state: dict) -> dict:
    """
    Analyze social impact of policy on different Indian population segments
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with social impact analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    
    prompt = f"""Answer in 8 words MAXIMUM per line. Use simple words.

Policy: {policy_text}

Answer format:
MIDDLE_CLASS_IMPACT:
LOWER_INCOME_IMPACT:
LIFESTYLE_CHANGES:"""

    response = response_text(generate(prompt))
    
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
    except:
        return ""
