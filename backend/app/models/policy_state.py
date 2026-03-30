from typing import TypedDict, Optional

class PolicyState(TypedDict):
    # input
    policy_text: str
    region: str

    # extracted understanding
    policy_type: Optional[str]
    sector: Optional[str]

    # agent outputs
    economic_impact: Optional[str]
    social_impact: Optional[str]
    business_impact: Optional[str]
    government_impact: Optional[str]

    # risk analysis
    protest_risk: Optional[str]
    risk_confidence: Optional[str]

    # explanation & reasoning
    explanation: Optional[str]

    # recommendation
    recommendation: Optional[str]