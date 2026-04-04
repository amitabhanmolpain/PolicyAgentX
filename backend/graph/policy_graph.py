from langgraph.graph import StateGraph
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


def run_economic_analysis(state: PolicyState) -> PolicyState:
    """Run economic agent and update state"""
    result = economic_agent(state)
    state["economic_analysis"] = result
    return state


def run_rag_retrieval(state: PolicyState) -> PolicyState:
    """Retrieve protest-aware RAG context and update state"""
    result = rag_node(state)
    state.update(result)
    return state


def run_social_analysis(state: PolicyState) -> PolicyState:
    """Run social agent and update state"""
    result = social_agent(state)
    state["social_analysis"] = result
    return state


def run_business_analysis(state: PolicyState) -> PolicyState:
    """Run business agent and update state"""
    result = business_agent(state)
    state["business_analysis"] = result
    return state


def run_government_analysis(state: PolicyState) -> PolicyState:
    """Run government agent and update state"""
    result = government_agent(state)
    state["government_analysis"] = result
    return state


def run_risk_analysis(state: PolicyState) -> PolicyState:
    """Run risk agent and update state"""
    result = risk_agent(state)
    state["risk_analysis"] = result
    return state


def run_recommendation(state: PolicyState) -> PolicyState:
    """Run recommendation agent and update state"""
    result = recommend_policy(state)
    state["recommendation"] = result
    return state


# Build the agent graph
builder = StateGraph(PolicyState)

builder.add_node("rag", run_rag_retrieval)
builder.add_node("economic", run_economic_analysis)
builder.add_node("social", run_social_analysis)
builder.add_node("business", run_business_analysis)
builder.add_node("government", run_government_analysis)
builder.add_node("risk", run_risk_analysis)
builder.add_node("recommendation", run_recommendation)

builder.set_entry_point("rag")

# All analyses run in parallel-like fashion (linear order for LangGraph)
builder.add_edge("rag", "economic")
builder.add_edge("economic", "social")
builder.add_edge("social", "business")
builder.add_edge("business", "government")
builder.add_edge("government", "risk")
builder.add_edge("risk", "recommendation")

graph = builder.compile()