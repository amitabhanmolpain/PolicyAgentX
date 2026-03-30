def analyze_policy(state):
    text = state["policy_text"]

    return {
        "analysis": f"Policy analyzed: {text}"
    }