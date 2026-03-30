from app.services.gemini_service import generate


def economic_agent(state: dict) -> dict:
    """
    Analyze economic impact of policy on India
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with economic analysis
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    
    prompt = f"""⚠️ IMPORTANT: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are an Indian economics expert analyzing government policies and their macroeconomic impacts on India's economy.

Policy: {policy_text}
Analysis Region: India (NOT any other country)

Analyze the ECONOMIC IMPACT of this policy specifically on India's economy. Provide specific, data-driven insights:

1. **GDP Impact**: Estimate percentage change in India's GDP growth rate (positive or negative). Which sectors/industries will be affected? Consider both short-term (0-6 months) and long-term (1-3 years) effects within the Indian context.

2. **Inflation Impact**: Estimate impact on India's inflation rate (CPI). Will this policy increase or decrease inflation in India? By how much? Consider Indian commodity prices and the Indian consumer basket.

3. **Employment Impact in India**: Estimate net jobs created or lost in India. Which Indian sectors will experience hiring increase/decrease? Consider India's formal and informal employment sectors.

Use Indian economic data, benchmarks, and conditions. Provide realistic numbers specific to India's economy.

Format your response as:
GDP_IMPACT: [percentage and explanation in Indian context]
INFLATION_IMPACT: [percentage and explanation for India]
EMPLOYMENT_IMPACT: [percentage and explanation for India]"""

    response = generate(prompt)
    
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
