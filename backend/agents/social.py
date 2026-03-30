from app.services.gemini_service import generate


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
    
    prompt = f"""⚠️ IMPORTANT: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are a social policy expert analyzing government policy impacts specifically on Indian society.

Policy: {policy_text}
Analysis Region: India (NOT any other country)

Analyze the SOCIAL IMPACT of this policy specifically on different population segments in India:

1. **Impact on Indian Middle Class**: How will this policy affect India's middle class (annual income 5-25 lakhs)? Will it improve or worsen their standard of living in the Indian context? Give specific examples of lifestyle changes relevant to Indian society.

2. **Impact on Lower Income Groups in India**: How will this affect economically weaker sections (EWS) and Below Poverty Line (BPL) populations in India? What hardships might occur? Which specific needs will be impacted (food, transportation, healthcare) for Indian families?

3. **Daily Life Changes for Indians**: What changes will Indians experience in their daily lives? Impact on Indian commuting costs, access to Indian goods, working conditions in Indian industries? Give concrete examples of tangible changes for Indian citizens.

Consider India's demographic structure, urban/rural divide, regional differences within India, and cultural factors in the Indian context.

Format your response as:
MIDDLE_CLASS_IMPACT: [specific impact percentage for Indian middle class]
LOWER_INCOME_IMPACT: [specific concerns for Indian poor and vulnerable]
LIFESTYLE_CHANGES: [concrete Indian examples of lifestyle changes]"""

    response = generate(prompt)
    
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
