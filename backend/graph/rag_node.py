from typing import Dict, List

from rag.policy_rag_retriever import PolicyRAGRetriever


def _extract_cases(context: str, limit: int = 3) -> List[str]:
    """Extract short historical protest case snippets from retrieved context."""
    lines = [line.strip("- \t") for line in (context or "").splitlines()]
    candidates = [line for line in lines if line and len(line) > 30]
    return candidates[:limit]


def _score_protest_risk(policy_text: str, context: str) -> int:
    """Heuristic 1-10 protest risk score based on policy terms + historical context."""
    score = 3
    text = (policy_text or "").lower()
    ctx = (context or "").lower()

    high_risk_terms = [
        "reservation", "quota", "farm", "farmer", "land", "language",
        "citizenship", "religion", "water", "cauvery", "protest", "strike",
    ]
    medium_risk_terms = [
        "tax", "price", "subsidy", "employment", "jobs", "education",
    ]

    if any(term in text for term in high_risk_terms):
        score += 3
    if any(term in text for term in medium_risk_terms):
        score += 2
    if any(term in ctx for term in ("bandh", "demonstration", "agitation", "supreme court", "violence")):
        score += 2

    return max(1, min(10, score))


def rag_node(state: Dict) -> Dict:
    """Retrieve protest context for the policy and attach it to graph state."""
    policy_text = state.get("policy_text", "")
    if not policy_text:
        return {
            "rag_context": "",
            "historical_protest_cases": [],
            "protest_risk_score": 1,
            "rag_source": "none",
        }

    retriever = PolicyRAGRetriever()
    historical_context = retriever.retrieve_historical_precedents(policy_type=policy_text, k=4)
    financial_context = retriever.retrieve_financial_context(policy_topic=policy_text, k=2)
    demo_context = retriever.retrieve_demographic_context(income_class="lower_middle", policy_topic=policy_text, k=2)

    combined_context = "\n\n".join([
        historical_context.strip(),
        financial_context.strip(),
        demo_context.strip(),
    ]).strip()

    cases = _extract_cases(combined_context, limit=3)
    protest_risk_score = _score_protest_risk(policy_text, combined_context)

    return {
        "rag_context": combined_context,
        "historical_protest_cases": cases,
        "protest_risk_score": protest_risk_score,
        "rag_source": retriever.persist_dir or "unknown",
    }