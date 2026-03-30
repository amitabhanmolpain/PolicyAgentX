class PolicyResult:
    def __init__(
        self,
        economic_impact,
        social_impact,
        business_impact,
        government_impact,
        protest_risk,
        risk_confidence,
        explanation,
        recommendation
    ):
        self.economic_impact = economic_impact
        self.social_impact = social_impact
        self.business_impact = business_impact
        self.government_impact = government_impact
        self.protest_risk = protest_risk
        self.risk_confidence = risk_confidence
        self.explanation = explanation
        self.recommendation = recommendation

    def to_dict(self):
        return {
            "economic_impact": self.economic_impact,
            "social_impact": self.social_impact,
            "business_impact": self.business_impact,
            "government_impact": self.government_impact,
            "protest_risk": self.protest_risk,
            "risk_confidence": self.risk_confidence,
            "explanation": self.explanation,
            "recommendation": self.recommendation
        }