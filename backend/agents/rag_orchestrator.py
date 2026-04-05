"""
RAG-Enhanced Agent Orchestrator
================================
Coordinates RAG pipeline, policy prediction engine, and specialized AI agents
for comprehensive policy analysis using LangGraph.
"""

import json
import re
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from copy import deepcopy

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

from rag.policy_rag_retriever import PolicyRAGRetriever
from agents.policy_predictor import PolicyPredictionEngine
from app.services.gemini_service import generate, response_text


@dataclass
class PolicyAnalysisState:
    """State passed through agent graph"""
    policy_text: str
    region: str = "India"
    
    # RAG Context
    financial_context: str = ""
    demographic_context: str = ""
    historical_context: str = ""
    economic_baseline: str = ""
    
    # Predictions
    financial_impact: Dict[str, Any] = None
    demographic_impact: List[Dict[str, Any]] = None
    future_projections: List[Dict[str, Any]] = None
    
    # Agent Analyses
    business_analysis: Dict[str, Any] = None
    economic_analysis: Dict[str, Any] = None
    government_analysis: Dict[str, Any] = None
    social_analysis: Dict[str, Any] = None
    risk_analysis: Dict[str, Any] = None
    recommendations: List[str] = None

    # Deep structured Gemini analysis
    policy_summary: Dict[str, Any] = None
    affected_groups: Dict[str, Any] = None
    economic_impact: Dict[str, Any] = None
    timeline: Dict[str, Any] = None
    global_impact: Dict[str, Any] = None
    protest_risk: Dict[str, Any] = None
    improvements: Dict[str, Any] = None
    frontend_cards: Dict[str, Any] = None
    
    # Final Report
    comprehensive_report: str = ""


class RAGEnhancedOrchestratorAgent:
    """Orchestrates RAG + Prediction Engine + Domain Agents"""
    
    def __init__(self):
        self.rag_retriever = PolicyRAGRetriever()
        self.prediction_engine = PolicyPredictionEngine()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("rag_context", self._rag_retrieval_node)
        workflow.add_node("deep_policy_analysis", self._deep_policy_analysis_node)
        workflow.add_node("prediction", self._prediction_node)
        workflow.add_node("business_agent", self._business_analysis_node)
        workflow.add_node("economic_agent", self._economic_analysis_node)
        workflow.add_node("government_agent", self._government_analysis_node)
        workflow.add_node("social_agent", self._social_analysis_node)
        workflow.add_node("risk_assessment", self._risk_assessment_node)
        workflow.add_node("recommendations", self._recommendations_node)
        workflow.add_node("final_report", self._generate_final_report_node)
        
        # Add edges - Sequential flow with parallel agent execution
        workflow.add_edge(START, "rag_context")
        workflow.add_edge("rag_context", "deep_policy_analysis")
        workflow.add_edge("deep_policy_analysis", "prediction")
        
        # Sequential execution avoids concurrent root-state writes on dict channels.
        workflow.add_edge("prediction", "business_agent")
        workflow.add_edge("business_agent", "economic_agent")
        workflow.add_edge("economic_agent", "government_agent")
        workflow.add_edge("government_agent", "social_agent")
        workflow.add_edge("social_agent", "risk_assessment")
        
        workflow.add_edge("risk_assessment", "recommendations")
        workflow.add_edge("recommendations", "final_report")
        workflow.add_edge("final_report", END)
        
        return workflow.compile()
    
    def _rag_retrieval_node(self, state: dict) -> dict:
        """Node 1: Retrieve RAG context"""
        policy_text = state.get("policy_text", "")
        
        # Detect policy type for better retrieval
        policy_type = self._detect_policy_type(policy_text)
        
        state["financial_context"] = self.rag_retriever.retrieve_financial_context(
            policy_type, k=5
        )
        state["demographic_context"] = "\n".join([
            self.rag_retriever.retrieve_demographic_context(income_class, policy_type)
            for income_class in ["upper", "middle", "lower_middle", "bpl"]
        ])
        state["historical_context"] = self.rag_retriever.retrieve_historical_precedents(
            policy_type, k=3
        )
        state["economic_baseline"] = self.rag_retriever.retrieve_economic_baseline(k=3)
        
        print("✅ RAG Context Retrieved")
        return state

    def _deep_policy_analysis_node(self, state: dict) -> dict:
        """Node 2: Single comprehensive Gemini JSON analysis using RAG context"""
        policy_text = state.get("policy_text", "")
        if not policy_text:
            return state

        rag_context = "\n\n".join([
            f"FINANCIAL_CONTEXT:\n{state.get('financial_context', '')}",
            f"DEMOGRAPHIC_CONTEXT:\n{state.get('demographic_context', '')}",
            f"HISTORICAL_CONTEXT:\n{state.get('historical_context', '')}",
            f"ECONOMIC_BASELINE:\n{state.get('economic_baseline', '')}",
        ])

        prompt = self._build_deep_policy_prompt(policy_text, rag_context)
        raw = response_text(generate(prompt, temperature=0.4, max_tokens=4096))
        parsed = self._parse_json_block(raw)

        if not parsed:
            parsed = self._default_deep_analysis(policy_text)

        normalized = self._normalize_deep_analysis(parsed)
        confidence_scores = self._compute_confidence_scores(normalized, rag_context)

        for key, score in confidence_scores.items():
            if isinstance(normalized.get(key), dict):
                normalized[key]["confidence_score"] = score

        state.update(normalized)
        state["frontend_cards"] = {
            "policy_summary": normalized.get("policy_summary", {}),
            "affected_groups": normalized.get("affected_groups", {}),
            "economic_impact": normalized.get("economic_impact", {}),
            "timeline": normalized.get("timeline", {}),
            "global_impact": normalized.get("global_impact", {}),
            "protest_risk": normalized.get("protest_risk", {}),
            "improvements": normalized.get("improvements", {}),
        }

        print("✅ Deep Structured Policy Analysis Complete")
        return state
    
    def _prediction_node(self, state: dict) -> dict:
        """Node 2: Generate predictions using policy prediction engine"""
        policy_text = state.get("policy_text", "")

        try:
            analysis = self.prediction_engine.comprehensive_policy_analysis(
                policy_text=policy_text,
                historical_context=state.get("financial_context", "")
            )

            state["financial_impact"] = asdict(analysis.financial_impact) if analysis.financial_impact else {}
            state["demographic_impact"] = [asdict(d) for d in analysis.demographic_impacts] if analysis.demographic_impacts else []
            state["future_projections"] = [asdict(p) for p in analysis.future_projections] if analysis.future_projections else []
        except Exception as e:
            state["financial_impact"] = state.get("financial_impact") or {}
            state["demographic_impact"] = state.get("demographic_impact") or []
            state["future_projections"] = state.get("future_projections") or []
            state["prediction_error"] = str(e)
            print(f"⚠️ Prediction engine fallback: {e}")
        
        print("✅ Predictions Generated")
        return state
    
    def _business_analysis_node(self, state: dict) -> dict:
        """Node 3a: Business Agent with RAG context"""
        policy_text = state.get("policy_text", "")
        context = state.get("financial_context", "")
        
        prompt = f"""You are a business policy analyst. Analyze this policy using provided context.

POLICY: {policy_text}

CONTEXT:
{context}

Provide brief analysis on:
1. SMALL_BUSINESS_IMPACT
2. LARGE_INDUSTRY_IMPACT
3. SUPPLY_CHAIN_EFFECT

Format: Each on one line, max 15 words."""
        
        response = response_text(generate(prompt))
        
        state["business_analysis"] = {
            "analysis": response,
            "small_business": self._extract_line(response, "SMALL_BUSINESS_IMPACT"),
            "large_industry": self._extract_line(response, "LARGE_INDUSTRY_IMPACT"),
            "supply_chain": self._extract_line(response, "SUPPLY_CHAIN_EFFECT"),
        }
        
        print("✅ Business Analysis Complete")
        return state
    
    def _economic_analysis_node(self, state: dict) -> dict:
        """Node 3b: Economic Agent with RAG context"""
        policy_text = state.get("policy_text", "")
        context = state.get("economic_baseline", "")
        
        prompt = f"""You are an economic analyst. Analyze this policy impact.

POLICY: {policy_text}

ECONOMIC_BASELINE:
{context}

Predict impact on:
1. GDP_GROWTH
2. INFLATION_RATE
3. EMPLOYMENT

Format: Each on one line, max 15 words."""
        
        response = response_text(generate(prompt))
        
        state["economic_analysis"] = {
            "analysis": response,
            "gdp_growth": self._extract_line(response, "GDP_GROWTH"),
            "inflation": self._extract_line(response, "INFLATION_RATE"),
            "employment": self._extract_line(response, "EMPLOYMENT"),
        }
        
        print("✅ Economic Analysis Complete")
        return state
    
    def _government_analysis_node(self, state: dict) -> dict:
        """Node 3c: Government Agent with RAG context"""
        policy_text = state.get("policy_text", "")
        financial_impact = state.get("financial_impact", {})
        
        prompt = f"""You are a government finance analyst. Assess fiscal impact.

POLICY: {policy_text}

PREDICTED_REVENUE_IMPACT: ₹{financial_impact.get('net_impact', 'N/A')} Cr

Assess:
1. REVENUE_GENERATION
2. FISCAL_VIABILITY
3. IMPLEMENTATION_FEASIBILITY

Format: Each on one line, max 15 words."""
        
        response = response_text(generate(prompt))
        
        state["government_analysis"] = {
            "analysis": response,
            "revenue": self._extract_line(response, "REVENUE_GENERATION"),
            "viability": self._extract_line(response, "FISCAL_VIABILITY"),
            "feasibility": self._extract_line(response, "IMPLEMENTATION_FEASIBILITY"),
        }
        
        print("✅ Government Analysis Complete")
        return state
    
    def _social_analysis_node(self, state: dict) -> dict:
        """Node 3d: Social Impact Agent"""
        policy_text = state.get("policy_text", "")
        demographic_context = state.get("demographic_context", "")
        demographic_impact = state.get("demographic_impact", [])
        
        income_impacts = "\n".join([
            f"- {d.get('income_class')}: net benefit/person ₹{d.get('net_benefit_per_person', 'N/A')}"
            for d in demographic_impact
        ]) if demographic_impact else "No demographic data"
        
        prompt = f"""You are a social policy analyst. Assess social impact.

POLICY: {policy_text}

INCOME_CLASS_IMPACT:
{income_impacts}

DEMOGRAPHIC_CONTEXT:
{demographic_context}

Evaluate:
1. SOCIAL_EQUITY
2. VULNERABLE_GROUPS_IMPACT
3. PUBLIC_ACCEPTANCE

Format: Each on one line, max 15 words."""
        
        response = response_text(generate(prompt))
        
        state["social_analysis"] = {
            "analysis": response,
            "equity": self._extract_line(response, "SOCIAL_EQUITY"),
            "vulnerable": self._extract_line(response, "VULNERABLE_GROUPS_IMPACT"),
            "acceptance": self._extract_line(response, "PUBLIC_ACCEPTANCE"),
        }
        
        print("✅ Social Analysis Complete")
        return state
    
    def _risk_assessment_node(self, state: dict) -> dict:
        """Node 5: Identify risks and challenges"""
        policy_text = state.get("policy_text", "")
        analyses = [
            state.get("business_analysis", {}),
            state.get("economic_analysis", {}),
            state.get("government_analysis", {}),
            state.get("social_analysis", {}),
        ]
        
        all_analysis = "\n".join([
            str(a) for a in analyses if a
        ])
        historical_context = state.get("historical_context", "")
        protest_risk_score = self._estimate_protest_risk_score(policy_text, historical_context)
        
        prompt = f"""Identify top 5 RISKS and MITIGATION for this policy:

POLICY: {policy_text}

AGENT_ANALYSES:
{all_analysis}

HISTORICAL_PROTEST_CONTEXT:
{historical_context}

For each risk, provide:
RISK_<number>: [Risk description]
MITIGATION_<number>: [How to mitigate]"""
        
        response = response_text(generate(prompt))
        
        state["risk_analysis"] = {
            "assessment": response,
            "risks": self._extract_risks(response),
            "protest_risk_score": protest_risk_score,
        }
        
        print("✅ Risk Assessment Complete")
        return state
    
    def _recommendations_node(self, state: dict) -> dict:
        """Node 6: Generate recommendations"""
        policy_text = state.get("policy_text", "")
        risk_analysis = state.get("risk_analysis", {})
        
        prompt = f"""Based on comprehensive analysis, provide TOP 5 RECOMMENDATIONS.

POLICY: {policy_text}

IDENTIFIED_RISKS:
{risk_analysis.get('assessment', '')}

Provide actionable recommendations as:
1. [First recommendation]
2. [Second recommendation]
3. [Third recommendation]
4. [Fourth recommendation]
5. [Fifth recommendation]"""
        
        response = response_text(generate(prompt))
        
        state["recommendations"] = self._extract_recommendations(response)
        
        print("✅ Recommendations Generated")
        return state
    
    def _generate_final_report_node(self, state: dict) -> dict:
        """Node 7: Generate comprehensive final report"""
        report = self._format_report(state)
        state["comprehensive_report"] = report
        
        print("✅ Final Report Generated")
        return state
    
    def analyze_policy(self, policy_text: str, region: str = "India") -> dict:
        """Execute full orchestration pipeline"""
        initial_state = {
            "policy_text": policy_text,
            "region": region,
            "financial_context": "",
            "demographic_context": "",
            "historical_context": "",
            "economic_baseline": "",
            "financial_impact": None,
            "demographic_impact": None,
            "future_projections": None,
            "business_analysis": None,
            "economic_analysis": None,
            "government_analysis": None,
            "social_analysis": None,
            "risk_analysis": None,
            "recommendations": None,
            "policy_summary": None,
            "affected_groups": None,
            "economic_impact": None,
            "timeline": None,
            "global_impact": None,
            "protest_risk": None,
            "improvements": None,
            "frontend_cards": None,
            "comprehensive_report": "",
        }
        
        result = self.graph.invoke(initial_state)
        return result
    
    # Helper Methods
    
    def _detect_policy_type(self, policy_text: str) -> str:
        """Detect policy type for better RAG retrieval"""
        keywords = {
            "tax": "taxation",
            "income": "income_tax",
            "gst": "gst",
            "education": "education",
            "health": "healthcare",
            "welfare": "social_welfare",
            "employment": "employment",
            "environment": "environmental",
            "agriculture": "agricultural",
        }
        
        policy_lower = policy_text.lower()
        for keyword, policy_type in keywords.items():
            if keyword in policy_lower:
                return policy_type
        
        return "general_policy"
    
    def _extract_line(self, text: str, prefix: str) -> str:
        """Extract a line starting with prefix"""
        for line in text.split("\n"):
            if prefix in line:
                return line.split(":", 1)[-1].strip()
        return ""

    def _extract_rupee_amount(self, policy_text: str) -> float:
        """Extract rupee-denominated amount from policy text, return INR value."""
        text = (policy_text or "").lower()
        match = re.search(r"(?:rs\.?|rupee|rupees)\s*([\d,]+(?:\.\d+)?)", text)
        if not match:
            return 0.0
        try:
            return float(match.group(1).replace(",", ""))
        except Exception:
            return 0.0

    def _infer_population_base(self, policy_text: str) -> int:
        """Infer a realistic total target population base (India) from policy theme."""
        text = (policy_text or "").lower()

        # Approximate India-scale reference bands by domain, tuned for policy simulation.
        if any(k in text for k in ["farmer", "agri", "kisan", "rural"]):
            return 110_000_000
        if any(k in text for k in ["immigrant", "migrant", "migration"]):
            return 65_000_000
        if any(k in text for k in ["student", "education", "school", "college"]):
            return 260_000_000
        if any(k in text for k in ["women", "maternal", "girl child"]):
            return 680_000_000
        if any(k in text for k in ["tax", "gst", "income tax"]):
            return 180_000_000
        if any(k in text for k in ["health", "hospital", "insurance"]):
            return 400_000_000
        if any(k in text for k in ["employment", "jobs", "reservation", "quota"]):
            return 220_000_000
        return 150_000_000

    def _infer_coverage_ratio(self, policy_text: str) -> float:
        """Estimate what share of the base group is likely covered by policy."""
        text = (policy_text or "").lower()
        ratio = 0.24
        if any(k in text for k in ["all", "universal", "nationwide"]):
            ratio = 0.55
        elif any(k in text for k in ["low income", "poor", "below poverty", "backward", "targeted"]):
            ratio = 0.28
        elif any(k in text for k in ["pilot", "phase", "phased"]):
            ratio = 0.12
        return max(0.08, min(0.65, ratio))

    def _format_india_people_count(self, count: int) -> str:
        """Format people count into readable India number style."""
        if count >= 10_000_000:
            return f"{round(count / 10_000_000, 2)} crore people (~{count:,})"
        if count >= 100_000:
            return f"{round(count / 100_000, 2)} lakh people (~{count:,})"
        return f"{count:,} people"

    def _format_inr_lakh_crore(self, amount_inr: float) -> str:
        """Format INR amount with crore/lakh units."""
        if amount_inr >= 10_000_000:
            return f"{round(amount_inr / 10_000_000, 2)} crores"
        if amount_inr >= 100_000:
            return f"{round(amount_inr / 100_000, 2)} lakhs"
        return f"{round(amount_inr, 2)} rupees"

    def _estimate_policy_financials(self, policy_text: str) -> Dict[str, str]:
        """Estimate people impacted and spend/generate ranges from policy text."""
        base_population = self._infer_population_base(policy_text)
        coverage_ratio = self._infer_coverage_ratio(policy_text)
        impacted_people = int(base_population * coverage_ratio)

        monthly_amount = self._extract_rupee_amount(policy_text)
        if monthly_amount <= 0:
            # Domain-sensitive monthly/annual support proxy when amount absent.
            text = (policy_text or "").lower()
            if any(k in text for k in ["health", "insurance"]):
                monthly_amount = 1200
            elif any(k in text for k in ["education", "student"]):
                monthly_amount = 900
            elif any(k in text for k in ["employment", "skill", "jobs"]):
                monthly_amount = 1500
            else:
                monthly_amount = 1000

        annual_spend = impacted_people * monthly_amount * 12.0
        year1_spend = annual_spend * 0.55
        year23_spend = annual_spend * 1.35
        year5_spend = annual_spend * 1.9
        year10_spend = annual_spend * 2.8

        # Conservative modeled productivity/revenue backflow from year 5 onward.
        year5_generate = annual_spend * 0.85
        year10_generate = annual_spend * 1.35

        return {
            "total_people_impacted_india": self._format_india_people_count(impacted_people),
            "required_public_spend_inr": self._format_inr_lakh_crore(annual_spend),
            "year_1_money": f"SPEND {self._format_inr_lakh_crore(year1_spend)}",
            "year_2_3_money": f"SPEND {self._format_inr_lakh_crore(year23_spend)}",
            "year_5_money": f"GENERATE {self._format_inr_lakh_crore(year5_generate)}",
            "year_10_money": f"GENERATE {self._format_inr_lakh_crore(year10_generate)}",
            "revenue_generated_inr_crores": f"{round((year5_generate + year10_generate) / 10_000_000, 2)}",
        }

    def _build_deep_policy_prompt(self, policy_text: str, rag_context: str) -> str:
        """Build a strict JSON prompt for comprehensive 7-section analysis."""
        return f"""You are India's best policy analyst. Analyze this policy in SIMPLE, CLEAR, EASY words.
Keep all explanations short and direct. Avoid complex jargon.

Policy to analyze:
{policy_text}

Historical context from database:
{rag_context}

Return VALID JSON ONLY with exactly these top-level keys:
- policy_summary
- affected_groups
- economic_impact
- timeline
- global_impact
- protest_risk
- improvements

SIMPLE REQUIREMENTS (use plain English):

1) policy_summary:
   - simple_meaning: What does this policy do? (2-3 sentences)
   - issuing_ministry: Which ministry runs this?
   - implementation_timeline: When will it happen?
    - total_people_impacted_india: Total people this policy likely affects in India (numeric + unit)

2) affected_groups:
    - groups: array with group_name, population_impact_percent, estimated_population_count, status (BENEFITED or OPPRESSED), reason
   - Keep reasons SHORT and CLEAR
    - Estimate how many people are in each group using crores or lakhs where possible

3) economic_impact:
   - gdp_impact_percent: Will it help the economy? By how much?
   - revenue_generated_inr_crores: How much money will the government make?
    - required_public_spend_inr: How much public money is needed to run this policy (lakhs/crores)
   - tax_collection_impact: Will taxes go up or down?
   - employment_impact_jobs: How many jobs created or lost?
   - inflation_risk (High/Medium/Low): Will prices go up?
   - fiscal_deficit_impact: Will government lose money?

4) timeline (MONEY IN OR OUT):
   - year_1, year_2_3, year_5, year_10
   Each year object needs:
     immediate_effect: What happens first? (simple words)
     adoption_or_growth: How many people will use it?
        inr_crore_estimate: Will it spend money or generate money? (say SPEND or GENERATE with amount and crore/lakh unit)
     EXAMPLE: "SPEND 5000 crores" or "GENERATE 2000 crores"

5) global_impact:
   - india_global_position: Will this help India's world standing?
   - fdi_impact: Will foreign companies invest more?
   - trade_balance_impact: Will exports/imports change?
   - comparison_usa_china_eu: How does this compare to other countries?
   - world_bank_imf_reaction: Will international organizations like this?
   - competitiveness_score_change: Will India do better vs other countries?

6) protest_risk:
   - risk_score_1_to_10 (1=very safe, 10=major protests)
   - likely_protesting_groups
   - high_risk_states_cities
   - historical_similar_protests

7) improvements:
   - three_bold_improvements (3 ways to make this better)
   - lower_protest_risk_modified_version: How to change it so fewer people oppose?
   - phased_rollout_recommendation: Should we do it all at once or slowly?

IMPORTANT:
- Use simple words a student can understand
- Include numeric INR amounts with units (lakhs/crores), no vague placeholders
- Use SPEND or GENERATE with numeric amount and units
- Be direct and clear
- Do not return markdown, only JSON"""

    def _parse_json_block(self, text: str) -> Dict[str, Any]:
        """Parse first valid JSON object from model text."""
        if not text:
            return {}
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return {}
        return {}

    def _default_deep_analysis(self, policy_text: str) -> Dict[str, Any]:
        """Fallback deep-analysis structure when model JSON parsing fails."""
        est = self._estimate_policy_financials(policy_text)
        return {
            "policy_summary": {
                "simple_meaning": f"Policy under analysis: {policy_text[:180]}",
                "issuing_ministry": "To be determined from policy text",
                "implementation_timeline": "Phased implementation recommended",
                "total_people_impacted_india": est.get("total_people_impacted_india", "Not estimated"),
            },
            "affected_groups": {"groups": []},
            "economic_impact": {
                "gdp_impact_percent": "0.0% to +0.5%",
                "revenue_generated_inr_crores": est.get("revenue_generated_inr_crores", "0"),
                "required_public_spend_inr": est.get("required_public_spend_inr", "Not estimated"),
                "tax_collection_impact": "Moderate",
                "employment_impact_jobs": "+100000 to +500000",
                "inflation_risk": "Medium",
                "fiscal_deficit_impact": "Manageable if phased",
            },
            "timeline": {
                "year_1": {"immediate_effect": "Setup starts", "adoption_or_growth": "30-45%", "inr_crore_estimate": est.get("year_1_money", "SPEND Not estimated")},
                "year_2_3": {"immediate_effect": "Grows bigger", "adoption_or_growth": "55-75%", "inr_crore_estimate": est.get("year_2_3_money", "SPEND Not estimated")},
                "year_5": {"immediate_effect": "Working well", "adoption_or_growth": "75-90%", "inr_crore_estimate": est.get("year_5_money", "GENERATE Not estimated")},
                "year_10": {"immediate_effect": "Stable and running", "adoption_or_growth": "85-95%", "inr_crore_estimate": est.get("year_10_money", "GENERATE Not estimated")},
            },
            "global_impact": {
                "india_global_position": "Potential incremental improvement",
                "fdi_impact": "Neutral to mildly positive",
                "trade_balance_impact": "Sector-dependent",
                "comparison_usa_china_eu": "Requires policy benchmarking",
                "world_bank_imf_reaction": "Positive if fiscally disciplined",
                "competitiveness_score_change": "+0.2 to +0.8",
            },
            "protest_risk": {
                "risk_score_1_to_10": 5,
                "likely_protesting_groups": ["Policy-affected opposition groups"],
                "high_risk_states_cities": ["High-sensitivity urban centers"],
                "historical_similar_protests": ["Issue-specific protest precedents"],
            },
            "improvements": {
                "three_bold_improvements": [
                    "Target benefits using dynamic eligibility signals",
                    "Deploy district-level phased rollout with live dashboards",
                    "Protect vulnerable groups via compensatory transfers",
                ],
                "lower_protest_risk_modified_version": "Pilot-first model with grievance redressal and safeguards",
                "phased_rollout_recommendation": "Pilot 6 months, expand 18 months, optimize quarterly",
            },
        }

    def _normalize_deep_analysis(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required top-level keys exist with dict values."""
        required = [
            "policy_summary",
            "affected_groups",
            "economic_impact",
            "timeline",
            "global_impact",
            "protest_risk",
            "improvements",
        ]
        fallback = self._default_deep_analysis("")
        out = {}
        for key in required:
            value = parsed.get(key)
            if isinstance(value, dict):
                out[key] = value
            else:
                out[key] = deepcopy(fallback[key])
        return out

    def _compute_confidence_scores(self, sections: Dict[str, Any], rag_context: str) -> Dict[str, int]:
        """Compute confidence score (0-100) per section from RAG signal overlap."""
        section_keywords = {
            "policy_summary": ["policy", "ministry", "timeline", "implementation"],
            "affected_groups": ["income", "class", "population", "rural", "urban", "farmer", "women", "sc", "st", "obc"],
            "economic_impact": ["gdp", "inflation", "revenue", "tax", "employment", "deficit"],
            "timeline": ["year", "phase", "adoption", "growth"],
            "global_impact": ["fdi", "trade", "world bank", "imf", "usa", "china", "eu", "competitiveness"],
            "protest_risk": ["protest", "agitation", "bandh", "unrest", "state", "city"],
            "improvements": ["improve", "modified", "rollout", "phased", "mitigation"],
        }
        rag = (rag_context or "").lower()
        scores = {}

        for key, words in section_keywords.items():
            text_blob = json.dumps(sections.get(key, {}), ensure_ascii=False).lower()
            support_hits = sum(1 for w in words if w in rag)
            response_hits = sum(1 for w in words if w in text_blob)

            base = 35
            support_component = min(45, support_hits * 6)
            response_component = min(20, response_hits * 3)
            scores[key] = max(0, min(100, base + support_component + response_component))

        return scores
    
    def _extract_risks(self, text: str) -> List[str]:
        """Extract risk items from response"""
        risks = []
        for line in text.split("\n"):
            if "RISK_" in line and ":" in line:
                risk = line.split(":", 1)[-1].strip()
                if risk:
                    risks.append(risk)
        return risks[:5]
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from numbered list"""
        recommendations = []
        for line in text.split("\n"):
            if line.strip() and line[0].isdigit() and "." in line:
                rec = line.split(".", 1)[-1].strip()
                if rec:
                    recommendations.append(rec)
        return recommendations[:5]

    def _estimate_protest_risk_score(self, policy_text: str, historical_context: str) -> int:
        """Estimate a protest risk score (1-10) from policy text + RAG context."""
        score = 3
        text = (policy_text or "").lower()
        ctx = (historical_context or "").lower()

        if any(term in text for term in ["reservation", "farm", "language", "citizenship", "water", "quota"]):
            score += 3
        if any(term in text for term in ["tax", "subsidy", "price", "employment"]):
            score += 2
        if any(term in ctx for term in ["protest", "bandh", "agitation", "demonstration", "violence"]):
            score += 2

        return max(1, min(10, score))
    
    def _format_report(self, state: dict) -> str:
        """Format comprehensive final report"""
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              COMPREHENSIVE POLICY ANALYSIS REPORT                         ║
║                    RAG + AI Agent Orchestration                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 POLICY SUMMARY
─────────────────────────────────────────────────────────────────────────────
{state.get('policy_text', '')[:500]}

🎯 FINANCIAL IMPACT
─────────────────────────────────────────────────────────────────────────────
{self._format_dict(state.get('financial_impact', {}))}

👥 DEMOGRAPHIC IMPACT BY INCOME CLASS
─────────────────────────────────────────────────────────────────────────────"""
        
        for impact in state.get("demographic_impact", []):
            report += f"\n{impact.get('income_class')}: {impact.get('impact', 'Unknown')}"
        
        report += f"""

📊 BUSINESS ANALYSIS
─────────────────────────────────────────────────────────────────────────────
{self._format_dict(state.get('business_analysis', {}))}

💹 ECONOMIC ANALYSIS
─────────────────────────────────────────────────────────────────────────────
{self._format_dict(state.get('economic_analysis', {}))}

🏛️  GOVERNMENT ANALYSIS
─────────────────────────────────────────────────────────────────────────────
{self._format_dict(state.get('government_analysis', {}))}

🤝 SOCIAL ANALYSIS
─────────────────────────────────────────────────────────────────────────────
{self._format_dict(state.get('social_analysis', {}))}

⚠️  RISK ASSESSMENT
─────────────────────────────────────────────────────────────────────────────
{self._format_list(state.get('risk_analysis', {}).get('risks', []))}

🧠 STRUCTURED JSON ANALYSIS
─────────────────────────────────────────────────────────────────────────────
{json.dumps(state.get('frontend_cards', {}), indent=2, ensure_ascii=False)[:3000]}

✅ RECOMMENDATIONS
─────────────────────────────────────────────────────────────────────────────
{self._format_list(state.get('recommendations', []))}

═════════════════════════════════════════════════════════════════════════════
Generated by: RAG + AI Agent Orchestrator
Date: {self._get_timestamp()}
═════════════════════════════════════════════════════════════════════════════
"""
        return report
    
    def _format_dict(self, d: dict) -> str:
        """Format dictionary for report"""
        if not d:
            return "No data available"
        return "\n".join([f"  • {k}: {v}" for k, v in d.items() if k != "analysis"])
    
    def _format_list(self, items: List[str]) -> str:
        """Format list for report"""
        if not items:
            return "No items"
        return "\n".join([f"  {i+1}. {item}" for i, item in enumerate(items)])
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
