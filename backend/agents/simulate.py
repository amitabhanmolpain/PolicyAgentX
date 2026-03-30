def simulate_policy(state):
    text = state["policy_text"]

    
    if "tax" in text.lower():
        simulation = """
Simulation Results:

GDP Impact: +2.5%
Inflation Impact: +1.3%
Government Revenue: -40%
Employment Change: +0.5%
"""
    else:
        simulation = """
Simulation Results:

GDP Impact: +1%
Inflation Impact: +0.5%
Employment Change: +0.2%
"""

    return {
        "simulation": simulation
    }