import json
import re
import logging
from rag.gemini_client import generate_async
from app.services.gemini_service import response_text

logger = logging.getLogger(__name__)

def _parse_json_safely(text: str) -> dict:
    """Parse JSON safely from raw LLM output, extracting from markdown code blocks if necessary."""
    cleaned = text.strip()
    # Remove markdown code block symbols if model wrapped output in ```json ... ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"Failed to parse risk agent JSON output directly: {e}. Attempting manual extraction.")
        # Fallback regex extraction of fields if the JSON was malformed
        extracted = {}
        for key in ["conflict_risk_score", "is_alert", "reasoning", "severity"]:
            # Match string fields
            str_match = re.search(rf'"{key}"\s*:\s*"([^"]*)"', cleaned)
            if str_match:
                extracted[key] = str_match.group(1)
            # Match numeric fields
            num_match = re.search(rf'"{key}"\s*:\s*(\d+)', cleaned)
            if num_match:
                extracted[key] = int(num_match.group(1))
            # Match boolean fields
            bool_match = re.search(rf'"{key}"\s*:\s*(true|false)', cleaned, re.IGNORECASE)
            if bool_match:
                extracted[key] = bool_match.group(1).lower() == "true"
        
        # Match list fields like affected_groups
        list_match = re.search(r'"affected_groups"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
        if list_match:
            group_elements = re.findall(r'"([^"]*)"', list_match.group(1))
            extracted["affected_groups"] = group_elements
            
        return extracted

async def risk_agent(state: dict, web_context: str = "") -> dict:
    """
    Analyze protest risk and public reaction to policy in India using genuine reasoning.
    
    Args:
        state: Policy state with policy_text and region
        web_context: Optional Web context from search APIs
    
    Returns:
        Dictionary with structured risk assessment
    """
    policy_text = state.get("policy_text", "")
    region = state.get("region", "India")
    rag_context = state.get("rag_context", "")[:2000]
    historical_cases = state.get("historical_protest_cases", [])
    baseline_score = int(state.get("protest_risk_score", 5) or 5)
    
    if not web_context:
        web_context = state.get("web_contexts", {}).get("news_conflict", "")
    if not web_context:
        try:
            from rag.tavily_client import get_cached_web_context_async
            web_context = await get_cached_web_context_async(policy_text, "news_conflict")
        except Exception:
            web_context = ""

    prompt = f"""You are a political risk analyst specializing exclusively in Indian public sentiment, social movements, and protest dynamics in India.
Analyze this policy proposal:
{policy_text}

Analysis Region: India (NOT any other country - analyze ONLY Indian context)

Historical Protest Context from ChromaDB (Historical PDF Retrieval):
{rag_context}

Current News, Protests, and Public Unrest Context (Tavily):
{web_context}

Historical Protest Cases:
{historical_cases}

Assess the conflict and discrimination potential in India:
1. Targeting & Discrimination: Identify whether the policy targets, restricts, or discriminates against a specific group (occupation, religion, region, caste, gender, etc.) in the Indian context.
2. Severity: Judge the severity of this restriction: does it ban, exclude, or forcibly restrict a group's rights/livelihood, vs. merely regulate or tax them?
3. Precedents: Cross-reference retrieved historical conflict precedents from ChromaDB and Tavily news context.

Return a valid JSON object ONLY. Do not include any markdown styling, explanations, introduction, or formatting outside the JSON object.
JSON structure:
{{
  "conflict_risk_score": <integer between 0 and 100>,
  "is_alert": <boolean true or false>,
  "affected_groups": [<list of specific targeted groups, e.g. "Farmers", "General Category">],
  "reasoning": "<A concise explanation of the risk, targeting, and severity in the Indian context. Mention relevant historical or news context if applicable.>",
  "severity": "<"low" or "moderate" or "high" or "severe">"
}}

Note: Set "is_alert" to true if the severity is "high" or "severe" (such as outright bans or restrictions targeting specific groups)."""

    raw_response = response_text(await generate_async(prompt, temperature=0.2, max_tokens=2048))
    
    parsed_res = _parse_json_safely(raw_response)
    
    # Extract individual fields with robust fallbacks
    risk_score = parsed_res.get("conflict_risk_score", baseline_score * 10)
    # Map scale 1-10 to 0-100 if score is extremely low
    if risk_score <= 10 and risk_score > 0:
        risk_score *= 10
        
    severity = str(parsed_res.get("severity", "moderate")).lower()
    if severity not in ["low", "moderate", "high", "severe"]:
        severity = "moderate"
        
    # Programmatic enforcement of is_alert for high/severe cases
    is_alert = parsed_res.get("is_alert", False)
    if severity in ["high", "severe"]:
        is_alert = True
        
    affected_groups = parsed_res.get("affected_groups", [])
    if not isinstance(affected_groups, list):
        affected_groups = [str(affected_groups)]
        
    reasoning = parsed_res.get("reasoning", "No explanation available")
    
    result = {
        "conflict_risk_score": risk_score,
        "is_alert": is_alert,
        "affected_groups": affected_groups,
        "reasoning": reasoning,
        "severity": severity,
        # Maintain backward compatibility fields for any legacy graph checks
        "protest_likelihood": "HIGH" if severity in ["high", "severe"] else "MEDIUM" if severity == "moderate" else "LOW",
        "protest_risk_score": max(1, min(10, int(risk_score / 10))),
        "public_reaction": reasoning
    }
    
    return result
