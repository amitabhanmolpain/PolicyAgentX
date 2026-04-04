"""
RAG-Enhanced Agent Orchestrator
================================
Coordinates RAG pipeline, policy prediction engine, and specialized AI agents
for comprehensive policy analysis using LangGraph.
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

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
        workflow.add_edge("rag_context", "prediction")
        
        # Parallel agent execution
        workflow.add_edge("prediction", "business_agent")
        workflow.add_edge("prediction", "economic_agent")
        workflow.add_edge("prediction", "government_agent")
        workflow.add_edge("prediction", "social_agent")
        
        # Converge to risk assessment
        workflow.add_edge("business_agent", "risk_assessment")
        workflow.add_edge("economic_agent", "risk_assessment")
        workflow.add_edge("government_agent", "risk_assessment")
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
    
    def _prediction_node(self, state: dict) -> dict:
        """Node 2: Generate predictions using policy prediction engine"""
        policy_text = state.get("policy_text", "")
        
        analysis = self.prediction_engine.comprehensive_policy_analysis(
            policy_text=policy_text,
            historical_context=state.get("financial_context", "")
        )
        
        state["financial_impact"] = asdict(analysis.financial_impact) if analysis.financial_impact else {}
        state["demographic_impact"] = [asdict(d) for d in analysis.demographic_impacts] if analysis.demographic_impacts else []
        state["future_projections"] = [asdict(p) for p in analysis.future_projections] if analysis.future_projections else []
        
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
