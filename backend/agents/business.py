from app.services.gemini_service import generate


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
    
    prompt = f"""⚠️ IMPORTANT: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are a business analyst specializing exclusively in Indian commerce, Indian industries, and Indian policy impacts.

Policy: {policy_text}
Analysis Region: India (NOT any other country)

Analyze the BUSINESS IMPACT of this policy specifically on Indian commerce and Indian industries:

1. **Impact on Indian MSMEs (Small Businesses)**: How will this affect India's small and medium enterprises? Which Indian sectors (Indian retail, Indian manufacturing, Indian services) will be impacted? Will operational costs increase/decrease for Indian businesses? Percentage of Indian MSMEs negatively/positively impacted?

2. **Impact on Major Indian Industries**: Which major Indian industries (Indian automotive, Indian IT, Indian pharmaceuticals, Indian textiles, Indian agriculture, Indian energy) will be most affected? Will India's competitiveness improve or worsen? India's export/import implications?

3. **Indian Supply Chain & Logistics**: Will Indian transportation costs change? Will Indian supply chains be disrupted? How will Indian warehousing, Indian distribution, and Indian last-mile delivery be affected? Impact on Indian regional connectivity?

Provide specific examples from actual Indian industries and sectors. Use current Indian economic data. Consider India's economic conditions and Indian business environment.

Format your response as:
SMALL_BUSINESS_IMPACT: [specific impact on Indian MSMEs, affected Indian sectors, cost changes]
LARGE_INDUSTRY_IMPACT: [affected major Indian industries, India's competitiveness changes]
SUPPLY_CHAIN_IMPACT: [Indian logistics costs, Indian distribution changes, disruption level]"""

    response = generate(prompt)
    
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
