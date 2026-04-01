"""
Policy Impact Predictor & Financial Analyzer
==============================================
Predicts:
- Future policy impact (5-10 years)
- Revenue gains/losses
- Impact by income class
- Beneficiaries vs. sufferers
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from vertexai.generative_models import GenerativeModel


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class FinancialImpact:
    """Financial impact metrics"""
    estimated_revenue_crores: float
    revenue_per_capita: float
    implementation_cost: float
    net_impact: float
    confidence_level: int  # 0-100
    assumptions: List[str]


@dataclass
class DemographicImpact:
    """Impact segmented by income class"""
    income_class: str
    population_affected: int
    beneficiaries_percent: float
    sufferers_percent: float
    net_benefit_per_person: float
    key_impacts: List[str]


@dataclass
class FutureProjection:
    """5-10 year impact projection"""
    year: int
    gdp_impact_percent: float
    employment_jobs_gained: int
    inflation_impact: float
    tax_revenue_impact_crores: float


@dataclass
class PolicyAnalysis:
    """Complete policy analysis"""
    policy_name: str
    analysis_date: str
    financial_impact: FinancialImpact
    demographic_impacts: List[DemographicImpact]
    future_projections: List[FutureProjection]
    main_beneficiaries: List[str]
    main_sufferers: List[str]
    risk_factors: List[str]
    recommendations: List[str]


# ─────────────────────────────────────────────
# POLICY PREDICTION ENGINE
# ─────────────────────────────────────────────

class PolicyPredictionEngine:
    """AI-powered policy impact prediction"""
    
    def __init__(self):
        self.model = GenerativeModel("gemini-2.0-flash-001")
        self.india_population = 1400000000
        self.india_gdp_trillions = 3.5
    
    def predict_financial_impact(self, policy_text: str, 
                                historical_context: str = "") -> FinancialImpact:
        """Predict financial gain/loss from policy"""
        
        prompt = f"""You are an expert policy economist analyzing Indian government policies.

Policy to analyze:
{policy_text}

Historical context:
{historical_context}

Analyze the financial impact and provide EXACT NUMBERS:

Response format (JSON):
{{
    "estimated_revenue_crores": <number or null if loss>,
    "estimated_loss_crores": <number or null if gain>,
    "implementation_cost_crores": <number>,
    "revenue_per_capita_rupees": <number>,
    "confidence_level": <0-100>,
    "key_assumptions": [<list of assumptions>],
    "time_to_break_even_years": <number>
}}

IMPORTANT:
- Use only Indian government data/estimates
- If revenue uncertain, provide conservative estimate
- Consider both direct and indirect effects
- Account for implementation costs
- Assume 5% effective policy implementation rate (India avg)
"""
        
        response = self.model.generate_content(prompt)
        impact_data = self._parse_json_response(response.text)
        
        revenue = impact_data.get("estimated_revenue_crores", 0)
        loss = impact_data.get("estimated_loss_crores", 0)
        net = revenue - loss - impact_data.get("implementation_cost_crores", 0)
        
        return FinancialImpact(
            estimated_revenue_crores=revenue,
            revenue_per_capita=impact_data.get("revenue_per_capita_rupees", 0),
            implementation_cost=impact_data.get("implementation_cost_crores", 0),
            net_impact=net,
            confidence_level=int(impact_data.get("confidence_level", 50)),
            assumptions=impact_data.get("key_assumptions", [])
        )
    
    def predict_demographic_impact(self, policy_text: str,
                                  income_class: str) -> DemographicImpact:
        """Predict impact segmented by income class"""
        
        income_data = {
            "upper": {"population_share": 0.05, "income_range": "₹50L+"},
            "middle": {"population_share": 0.20, "income_range": "₹15-50L"},
            "lower_middle": {"population_share": 0.30, "income_range": "₹5-15L"},
            "bpl": {"population_share": 0.45, "income_range": "Below ₹5L"}
        }
        
        class_data = income_data.get(income_class, {})
        population = int(self.india_population * class_data.get("population_share", 0))
        
        prompt = f"""Analyze policy impact on {income_class.replace('_', ' ').upper()} class.

Policy:
{policy_text}

Income Class Details:
- Income Range: {class_data.get('income_range')}
- Population: {population:,} people ({class_data.get('population_share')*100:.0f}% of India)

Provide impact analysis in JSON:
{{
    "beneficiaries_percent": <0-100>,
    "sufferers_percent": <0-100>,
    "neutral_percent": <0-100>,
    "net_benefit_per_person_rupees": <number, negative if loss>,
    "key_positive_impacts": [<list>],
    "key_negative_impacts": [<list>],
    "severity_rating": <1-10>
}}

Focus on:
- Direct income/employment impact
- Cost of living effects
- Access to services
- Savings capacity """
        
        response = self.model.generate_content(prompt)
        impact_data = self._parse_json_response(response.text)
        
        return DemographicImpact(
            income_class=income_class,
            population_affected=population,
            beneficiaries_percent=float(impact_data.get("beneficiaries_percent", 0)),
            sufferers_percent=float(impact_data.get("sufferers_percent", 0)),
            net_benefit_per_person=float(impact_data.get("net_benefit_per_person_rupees", 0)),
            key_impacts=impact_data.get("key_positive_impacts", []) + 
                       [f"NEGATIVE: {x}" for x in impact_data.get("key_negative_impacts", [])]
        )
    
    def project_future_impact(self, policy_text: str, 
                             years: int = 5) -> List[FutureProjection]:
        """Project policy impact over 5-10 years"""
        
        prompt = f"""Project the impact of this policy over the next {years} years.

Policy:
{policy_text}

Provide year-by-year projections in JSON array format:
[
    {{
        "year": 2025,
        "gdp_impact_percent": <-/+>,
        "employment_jobs_gained": <number>,
        "inflation_impact_percent": <-/+>,
        "tax_revenue_impact_crores": <number>
    }},
    ...
]

Consider:
- Policy ramp-up time
- Market adjustments
- Behavioral changes
- Multiplier effects
- Phasing effects

Assume implementation starting Year 1 at 70% effectiveness, reaching 95% by Year 3."""
        
        response = self.model.generate_content(prompt)
        projections_data = self._parse_json_array(response.text)
        
        projections = []
        for proj in projections_data:
            projections.append(FutureProjection(
                year=int(proj.get("year", 2025)),
                gdp_impact_percent=float(proj.get("gdp_impact_percent", 0)),
                employment_jobs_gained=int(proj.get("employment_jobs_gained", 0)),
                inflation_impact=float(proj.get("inflation_impact_percent", 0)),
                tax_revenue_impact_crores=float(proj.get("tax_revenue_impact_crores", 0))
            ))
        
        return projections
    
    def comprehensive_policy_analysis(self, policy_text: str,
                                     historical_context: str = "") -> PolicyAnalysis:
        """Full analysis: financial + demographic + future"""
        
        print("🔍 Analyzing policy comprehensively...")
        print("  → Financial impact prediction...")
        financial = self.predict_financial_impact(policy_text, historical_context)
        
        print("  → Demographic segmentation...")
        demographic_impacts = []
        for income_class in ["upper", "middle", "lower_middle", "bpl"]:
            demo = self.predict_demographic_impact(policy_text, income_class)
            demographic_impacts.append(demo)
        
        print("  → Future impact projections...")
        future_projections = self.project_future_impact(policy_text, years=5)
        
        # Aggregate beneficiaries/sufferers
        main_beneficiaries = [
            demo.income_class for demo in demographic_impacts 
            if demo.beneficiaries_percent > demo.sufferers_percent
        ]
        main_sufferers = [
            demo.income_class for demo in demographic_impacts 
            if demo.sufferers_percent > demo.beneficiaries_percent
        ]
        
        # Risk assessment
        risk_factors = self._identify_risks(demographic_impacts, financial)
        
        # Recommendations
        recommendations = self._generate_recommendations(
            main_beneficiaries, main_sufferers, financial, demographic_impacts
        )
        
        return PolicyAnalysis(
            policy_name="Policy Analysis",
            analysis_date=datetime.now().isoformat(),
            financial_impact=financial,
            demographic_impacts=demographic_impacts,
            future_projections=future_projections,
            main_beneficiaries=main_beneficiaries,
            main_sufferers=main_sufferers,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    # ─────────────────────────────────────────────
    # UTILITY FUNCTIONS
    # ─────────────────────────────────────────────
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response"""
        try:
            # Find JSON object in response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        return {}
    
    def _parse_json_array(self, text: str) -> List[Dict]:
        """Extract JSON array from AI response"""
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        return []
    
    def _identify_risks(self, demos: List[DemographicImpact], 
                       fin: FinancialImpact) -> List[str]:
        """Identify implementation risks"""
        risks = []
        
        # High suffering groups
        for demo in demos:
            if demo.sufferers_percent > 60:
                risks.append(
                    f"HIGH RISK: {demo.income_class} class {demo.sufferers_percent:.0f}% will suffer"
                )
        
        # Budget concerns
        if fin.net_impact < -50000:
            risks.append(f"FISCAL: ₹{fin.net_impact:,.0f}Cr fiscal impact - needs funding source")
        
        # Low confidence
        if fin.confidence_level < 40:
            risks.append("MODEL: Low confidence prediction - limited historical data")
        
        return risks
    
    def _generate_recommendations(self, beneficiaries: List[str],
                                 sufferers: List[str],
                                 financial: FinancialImpact,
                                 demographics: List[DemographicImpact]) -> List[str]:
        """Generate policy recommendations"""
        recs = []
        
        if "bpl" in sufferers:
            recs.append("ADD: Targeted welfare schemes for below-poverty-line population")
        
        if "lower_middle" in sufferers:
            recs.append("MODIFY: Implement progressive taxation to shield lower-middle class")
        
        if financial.net_impact < 0:
            recs.append(f"FUND: Allocate ₹{abs(financial.implementation_cost):,.0f}Cr from other programs")
        
        if financial.confidence_level < 50:
            recs.append("PILOT: Start with state-level pilot program before national rollout")
        
        return recs


# ─────────────────────────────────────────────
# FORMATTING & REPORTING
# ─────────────────────────────────────────────

class PolicyAnalysisReporter:
    """Format policy analysis for display"""
    
    @staticmethod
    def format_financial_summary(impact: FinancialImpact) -> str:
        """Format financial metrics"""
        status = "💰 GAIN" if impact.net_impact >= 0 else "💸 LOSS"
        return f"""{status}
Revenue Impact: ₹{impact.estimated_revenue_crores:,.0f} Crores
Per Capita: ₹{impact.revenue_per_capita:,.0f}
Implementation Cost: ₹{impact.implementation_cost:,.0f} Crores
NET IMPACT: ₹{impact.net_impact:,.0f} Crores
Confidence: {impact.confidence_level}%"""
    
    @staticmethod
    def format_demographic_impact(impact: DemographicImpact) -> str:
        """Format demographic analysis"""
        suffix = "🟢 BENEFIT" if impact.net_benefit_per_person > 0 else "🔴 SUFFER"
        return f"""{suffix}: {impact.income_class.upper()}
Population: {impact.population_affected / 1000000:.1f}M
Benefit: {impact.beneficiaries_percent:.0f}% | Suffer: {impact.sufferers_percent:.0f}%
Per Person: ₹{impact.net_benefit_per_person:,.0f}
Key: {', '.join(impact.key_impacts[:2])}"""
    
    @staticmethod
    def format_policy_summary(analysis: PolicyAnalysis) -> str:
        """Format complete analysis"""
        output = f"""
╔════════════════════════════════════════════════════════════════╗
║                    POLICY IMPACT ANALYSIS                      ║
╚════════════════════════════════════════════════════════════════╝

FINANCIAL IMPACT:
{PolicyAnalysisReporter.format_financial_summary(analysis.financial_impact)}

DEMOGRAPHIC IMPACT:
"""
        for demo in analysis.demographic_impacts:
            output += f"\n{PolicyAnalysisReporter.format_demographic_impact(demo)}\n"
        
        output += f"""
MAIN BENEFICIARIES: {', '.join(analysis.main_beneficiaries) or 'None'}
MAIN SUFFERERS: {', '.join(analysis.main_sufferers) or 'None'}

FUTURE OUTLOOK (Year 1-5):
"""
        for proj in analysis.future_projections[:3]:
            output += f"  Year {proj.year}: GDP {proj.gdp_impact_percent:+.2f}%, "
            output += f"Jobs {proj.employment_jobs_gained:+,}, "
            output += f"Revenue ₹{proj.tax_revenue_impact_crores:+,.0f}Cr\n"
        
        output += f"""
RISKS: {', '.join(analysis.risk_factors) or 'Low risk'}

RECOMMENDATIONS:
"""
        for i, rec in enumerate(analysis.recommendations, 1):
            output += f"  {i}. {rec}\n"
        
        return output


# ─────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    engine = PolicyPredictionEngine()
    
    # Example policy
    sample_policy = """
    Proposed Policy: Increase income tax for income over ₹50 lakhs annually
    - Tax increase: 5% higher bracket
    - Expected to increase tax revenue by ₹15,000 crores
    - Phased implementation over 18 months
    """
    
    print("Analyzing policy impact...")
    analysis = engine.comprehensive_policy_analysis(sample_policy)
    
    # Print formatted report
    print(PolicyAnalysisReporter.format_policy_summary(analysis))
