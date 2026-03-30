from app.services.gemini_service import generate


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
    
    prompt = f"""⚠️ IMPORTANT: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are a fiscal policy and Indian government administration expert analyzing policy impacts on India's government operations and Indian government finances.

Policy: {policy_text}
Analysis Region: India (NOT any other country - analyze only INDIAN government impact)

Analyze the GOVERNMENT IMPACT of this policy specifically on India's government:

1. **Indian Government Revenue**: Will this policy increase or decrease India's government revenue? From which Indian revenue sources (Indian taxes, Indian fees, Indian duties)? Estimate revenue impact in Indian rupees or percentage terms. Consider both direct and indirect revenue effects on India's budget.

2. **Impact on Indian Fiscal Deficit**: Will this worsen or improve India's fiscal deficit? Explain why. Consider India's implementation costs, India's revenue collection challenges, and India's long-term fiscal sustainability.

3. **Policy Feasibility in India**: Can the Indian government realistically implement this policy? Consider:
   - Indian bureaucratic capacity and Indian administrative system
   - Enforcement challenges in Indian urban vs Indian rural areas
   - Indian technology/infrastructure requirements
   - Corruption/leakage risks in the Indian system
   - Estimated implementation timeline for India
   - Cost of implementation in the Indian context
   - Indian regulatory framework changes needed
   - Differences between central Indian government vs Indian state governments

Be realistic about Indian government capabilities and Indian government constraints. Consider Indian federal vs Indian state-level implementation separately.

Format your response as:
REVENUE_IMPACT: [Indian revenue change, Indian sources, estimated amount in rupees]
FISCAL_DEFICIT_IMPACT: [impact on India's deficit, reasoning for India]
FEASIBILITY: [feasibility for Indian government, Indian challenges, timeline, implementation cost]"""

    response = generate(prompt)
    
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
