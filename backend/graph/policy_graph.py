from typing import TypedDict

from agents.economic import economic_agent
from agents.social import social_agent
from agents.business import business_agent
from agents.government import government_agent
from agents.risk import risk_agent
from agents.recommend import recommend_policy
from graph.rag_node import rag_node


class PolicyState(TypedDict):
    policy_text: str
    region: str
    rag_context: str
    historical_protest_cases: list
    protest_risk_score: int
    rag_source: str
    economic_analysis: dict
    social_analysis: dict
    business_analysis: dict
    government_analysis: dict
    risk_analysis: dict
    recommendation: dict


def initialize_state(policy_text: str, region: str = "India") -> PolicyState:
    """Initialize policy state"""
    return {
        "policy_text": policy_text,
        "region": region,
        "rag_context": "",
        "historical_protest_cases": [],
        "protest_risk_score": 1,
        "rag_source": "",
        "economic_analysis": {},
        "social_analysis": {},
        "business_analysis": {},
        "government_analysis": {},
        "risk_analysis": {},
        "recommendation": {},
    }


def run_async_in_sync(coro):
    """Run an async coroutine inside a synchronous execution context."""
    import asyncio
    import concurrent.futures
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
        
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        return asyncio.run(coro)


def run_economic_analysis(state: PolicyState) -> PolicyState:
    """Run economic agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "economic")
    result = run_async_in_sync(economic_agent(state, web_context=web_context))
    state["economic_analysis"] = result
    return state


def run_rag_retrieval(state: PolicyState) -> PolicyState:
    """Retrieve protest-aware RAG context and update state"""
    result = rag_node(state)
    state.update(result)
    return state


def run_social_analysis(state: PolicyState) -> PolicyState:
    """Run social agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "news_conflict")
    result = run_async_in_sync(social_agent(state, web_context=web_context))
    state["social_analysis"] = result
    return state


def run_business_analysis(state: PolicyState) -> PolicyState:
    """Run business agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "general")
    result = run_async_in_sync(business_agent(state, web_context=web_context))
    state["business_analysis"] = result
    return state


def run_government_analysis(state: PolicyState) -> PolicyState:
    """Run government agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "government")
    result = run_async_in_sync(government_agent(state, web_context=web_context))
    state["government_analysis"] = result
    return state


def run_risk_analysis(state: PolicyState) -> PolicyState:
    """Run risk agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "news_conflict")
    result = run_async_in_sync(risk_agent(state, web_context=web_context))
    state["risk_analysis"] = result
    return state


def run_recommendation(state: PolicyState) -> PolicyState:
    """Run recommendation agent and update state"""
    from rag.tavily_client import get_cached_web_context
    web_context = get_cached_web_context(state.get("policy_text", ""), "general")
    result = run_async_in_sync(recommend_policy(state, web_context=web_context))
    state["recommendation"] = result
    return state


class PolicyGraph:
    """Minimal sequential graph wrapper that preserves graph.invoke(state)."""

    def invoke(self, state: PolicyState) -> PolicyState:
        state = run_rag_retrieval(state)
        state = run_economic_analysis(state)
        state = run_social_analysis(state)
        state = run_business_analysis(state)
        state = run_government_analysis(state)
        state = run_risk_analysis(state)
        state = run_recommendation(state)
        return state


graph = PolicyGraph()