from langgraph.graph import StateGraph
from typing import TypedDict

from agents.analyze import analyze_policy
from agents.simulate import simulate_policy
from agents.explain import explain_policy
from agents.recommend import recommend_policy

class PolicyState(TypedDict):
    policy_text: str
    analysis: str
    simulation: str
    explanation: str
    recommendation: str


builder = StateGraph(PolicyState)

builder.add_node("analyze", analyze_policy)
builder.add_node("simulate", simulate_policy)
builder.add_node("explain", explain_policy)
builder.add_node("recommend", recommend_policy)

builder.set_entry_point("analyze")

builder.add_edge("analyze", "simulate")
builder.add_edge("simulate", "explain")
builder.add_edge("explain", "recommend")

graph = builder.compile()