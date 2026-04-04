from app.services.gemini_service import generate, response_text


def recommend_policy(state: dict) -> dict:
    """
    Generate optimized policy recommendations based on analysis
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with policy recommendations
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:1800]
    historical_cases = state.get("historical_protest_cases", [])
    
    prompt = f"""⚠️ IMPORTANT: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are a senior policy advisor to the Indian government with expertise exclusively in Indian socio-economic policy design.

Original Policy: {policy_text}
Analysis Region: India (NOT any other country - provide recommendations ONLY for India)

Historical Protest Context from RAG:
{rag_context}

Historical Protest Cases:
{historical_cases}

Based on this policy for India, provide OPTIMIZED RECOMMENDATIONS for Indian government:

1. **Optimized Policy Version for India**: Propose a modified or better version of this policy specifically for India that:
   - Achieves the original policy's goals more effectively in the Indian context
   - Reduces negative impact on India's vulnerable populations
   - Increases political feasibility in India (lower protest risk among Indians)
   - Is realistic and implementable in India's system
   - Considers Indian regional variations if applicable
   
   Be specific: provide exact modifications, Indian percentages, Indian exemptions, phasing for India, etc.

2. **Why It's Better for India**: Explain why your proposed version is superior for the Indian context:
   - Better Indian economic outcomes (specify: India's GDP, India's inflation, India's employment impacts)
   - Indian social benefits (which Indian groups benefit more, reduced hardship for Indians)
   - Lower protest risk in India (which affected Indian groups are mollified)
   - Better India's fiscal impact
   - Easier to implement in the Indian system
   - Specific Indian improvements with Indian numbers/percentages

3. **Implementation Strategy for India**: 
   - Phasing approach and timeline for India
   - Which Indian states/regions to pilot first
   - Indian subsidy/support mechanisms for Indian vulnerable groups
   - Communication strategy to build Indian public support
   - Expected timeline to full implementation across India

Be realistic about Indian system constraints. Ground recommendations in Indian policy precedents and feasible Indian implementation approaches. Prioritize protecting India's vulnerable populations while achieving policy objectives for India.

Format your response as:
OPTIMIZED_POLICY: [detailed policy proposal for India]
WHY_BETTER: [comparative analysis for India with specific metrics]
IMPLEMENTATION: [phasing for India, Indian pilot regions, Indian support mechanisms, timeline]"""

    response = response_text(generate(prompt, temperature=0.7, max_tokens=2500))
    
    result = {
        "recommendation_analysis": response,
        "optimized_policy": _extract_section(response, "OPTIMIZED_POLICY"),
        "why_better": _extract_section(response, "WHY_BETTER"),
        "implementation_strategy": _extract_section(response, "IMPLEMENTATION"),
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