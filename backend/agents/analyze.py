def analyze_policy(state):
    text = state["policy_text"]

    analysis = f"""
Policy Analysis:

Policy: {text}

Detected Effects:
- Impacts economy
- Affects government revenue
- Influences public spending
"""

    return {
        "analysis": analysis
    }