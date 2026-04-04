from app.services.gemini_service import generate, response_text


def risk_agent(state: dict) -> dict:
    """
    Analyze protest risk and public reaction to policy in India
    
    Args:
        state: Policy state with policy_text and region
    
    Returns:
        Dictionary with risk assessment and protest likelihood
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:2000]
    historical_cases = state.get("historical_protest_cases", [])
    baseline_score = int(state.get("protest_risk_score", 5) or 5)
    
    prompt = f"""⚠️ CRITICAL: This analysis is STRICTLY FOR INDIAN GOVERNMENT POLICIES ONLY.

You are a political risk analyst specializing exclusively in Indian public sentiment, social movements, and protest dynamics in India.

Policy: {policy_text}
Analysis Region: India (NOT any other country - analyze ONLY Indian context)

Historical Protest Context from RAG:
{rag_context}

Historical Protest Cases:
{historical_cases}

Conduct a PROTEST RISK ANALYSIS for India. Assess the likelihood of public protests and civil unrest SPECIFICALLY in the Indian context:

1. **Likelihood of Protests in India**: What is the probability of public protests/civil unrest in India? Rate as:
   - LOW (0-20%): Indian general public acceptance, minimal opposition in Indian context
   - MEDIUM (20-60%): Moderate opposition from specific Indian groups, localized Indian protests possible
   - HIGH (60-100%): High likelihood of significant Indian protests, strikes, demonstrations across India
   
   Justify your rating with specific reasoning about Indian public sentiment.

2. **Affected Population Groups in India**: Which specific Indian groups will be most negatively affected?
   - Specific Indian income brackets (impact in Indian rupees/percentages)
   - Which Indian states/cities will be most affected
   - Which Indian industries/occupations most impacted
   - Indian social groups (Indian farmers, Indian workers, Indian students, etc.)
   - Estimate percentage of Indian population affected
   - Intensity of impact on each group in the Indian context

3. **Public Reaction in India**: 
   - Historical precedent in India: Past Indian protests (fuel price protests, farm protests, quota protests, etc.)
   - Emotional triggers for Indian population: What will anger Indians? Past Indian grievances?
   - How Indian media will frame this politically
   - Indian social media amplification risk through Indian platforms
   - Indian opposition party response potential
   - Reference actual Indian social movements and Indian protest history

4. **Confidence Score**: How confident are you in this assessment for India? (70-95% confidence based on Indian political precedent)

5. **Protest Risk Score (1-10)**:
    - Use 1 for very low protest risk and 10 for extreme protest risk.
    - Baseline from retrieval heuristic: {baseline_score}

Be extremely specific with examples from INDIAN history ONLY. Extract only Indian precedents.

Format your response as:
PROTEST_LIKELIHOOD: [LOW/MEDIUM/HIGH with Indian context and percentage]
AFFECTED_GROUPS: [specific Indian groups, percentages, affected Indian states]
PUBLIC_REACTION: [emotional triggers for Indians, Indian historical parallels, Indian media narrative]
CONFIDENCE_SCORE: [percentage confidence in Indian context]
PROTEST_RISK_SCORE: [integer 1-10]"""

    response = response_text(generate(prompt, temperature=0.8, max_tokens=2500))
    
    result = {
        "risk_analysis": response,
        "protest_likelihood": _extract_protest_level(response),
        "protest_risk_score": _extract_risk_score(response, baseline_score),
        "affected_groups": _extract_section(response, "AFFECTED_GROUPS"),
        "public_reaction": _extract_section(response, "PUBLIC_REACTION"),
        "confidence_score": _extract_confidence(response),
    }
    
    return result


def _extract_protest_level(text: str) -> str:
    """Extract protest likelihood level"""
    try:
        start = text.find("PROTEST_LIKELIHOOD:")
        if start == -1:
            return "MEDIUM"
        start += len("PROTEST_LIKELIHOOD:") + 1
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        content = text[start:end].strip()
        
        if "HIGH" in content.upper():
            return "HIGH"
        elif "LOW" in content.upper():
            return "LOW"
        else:
            return "MEDIUM"
    except:
        return "MEDIUM"


def _extract_confidence(text: str) -> str:
    """Extract confidence score"""
    try:
        start = text.find("CONFIDENCE_SCORE:")
        if start == -1:
            return "75%"
        start += len("CONFIDENCE_SCORE:") + 1
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        return text[start:end].strip()
    except:
        return "75%"


def _extract_risk_score(text: str, fallback: int) -> int:
    """Extract numeric protest risk score from model response."""
    try:
        start = text.find("PROTEST_RISK_SCORE:")
        if start == -1:
            return max(1, min(10, fallback))
        start += len("PROTEST_RISK_SCORE:") + 1
        end = text.find("\n", start)
        if end == -1:
            end = len(text)
        raw = text[start:end].strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            return max(1, min(10, fallback))
        return max(1, min(10, int(digits[:2])))
    except:
        return max(1, min(10, fallback))


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
