def recommend_policy(state):
    text = state["policy_text"]

    if "remove income tax" in text.lower():
        recommendation = """
Recommendation:

Instead of completely removing income tax,
consider reducing it by 30%.

Reason:
- Maintains government revenue
- Still boosts consumer spending
"""
    else:
        recommendation = """
Recommendation:

Apply the policy gradually and monitor impact
before full implementation.
"""

    return {
        "recommendation": recommendation
    }