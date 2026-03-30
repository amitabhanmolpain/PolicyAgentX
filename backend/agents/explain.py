def explain_policy(state):
    simulation = state["simulation"]

    explanation = f"""
Explanation:

Based on the simulation:

- Increase in GDP is due to higher consumer spending
- Inflation rises because demand increases
- Government revenue may decrease due to tax reduction

Details:
{simulation}
"""

    return {
        "explanation": explanation
    }