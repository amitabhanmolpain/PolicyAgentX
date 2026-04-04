"""
RAG-Agent Orchestrator: Connects RAG pipeline with AI agents for comprehensive policy analysis
"""

from dataclasses import dataclass
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.policy_rag_retriever import PolicyRAGRetriever, analyze_policy_with_rag
from agents.policy_predictor import PolicyPredictionEngine


@dataclass
class AgentContext:
    """Context data passed between agents"""
    policy_description: str
    policy_type: str
    rag_context: Dict[str, Any]
    financial_analysis: Dict[str, Any] = None
    demographic_analysis: Dict[str, Any] = None
    social_impact: Dict[str, Any] = None
    economic_impact: Dict[str, Any] = None
    business_impact: Dict[str, Any] = None
    risk_factors: List[str] = None
    government_coordination: Dict[str, Any] = None


class RAGAgentOrchestrator:
    """Orchestrates collaboration between RAG retrieval and multiple AI agents"""
    
    def __init__(self):
        """Initialize orchestrator with RAG retriever and prediction engine"""
        try:
            self.rag_retriever = PolicyRAGRetriever()
            self.predictor = PolicyPredictionEngine()
            print("✓ RAG-Agent Orchestrator initialized")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize RAG components: {e}")
            self.rag_retriever = None
            self.predictor = None
    
    def orchestrate_policy_analysis(self, policy_description: str) -> Dict[str, Any]:
        """
        Orchestrate comprehensive policy analysis using RAG + all agents
        
        Args:
            policy_description: Description of the policy to analyze
            
        Returns:
            Comprehensive analysis with all agent outputs
        """
        
        print(f"\n{'='*70}")
        print(f"🔄 ORCHESTRATING POLICY ANALYSIS")
        print(f"{'='*70}\n")
        
        # Step 1: RAG Context Retrieval
        print("📚 Step 1: Retrieving RAG Context...")
        if not self.rag_retriever:
            rag_context = {
                "error": "RAG not available",
                "detected_type": self._detect_policy_type(policy_description),
                "financial_context": "",
                "demographic_context": "",
                "economic_context": "",
                "government_context": "",
            }
        else:
            try:
                context_text = self.rag_retriever.enhance_policy_with_context(policy_description)
                rag_context = {
                    "detected_type": self._detect_policy_type(policy_description),
                    "enhanced_context": context_text,
                    "financial_context": context_text,
                    "demographic_context": context_text,
                    "economic_context": context_text,
                    "government_context": context_text,
                }
            except Exception as e:
                rag_context = {
                    "error": f"RAG retrieval failed: {e}",
                    "detected_type": self._detect_policy_type(policy_description),
                    "financial_context": "",
                    "demographic_context": "",
                    "economic_context": "",
                    "government_context": "",
                }
        
        # Initialize agent context
        agent_context = AgentContext(
            policy_description=policy_description,
            policy_type=rag_context.get("detected_type", "general"),
            rag_context=rag_context
        )
        
        # Step 2: Financial Agent Analysis
        print("\n💰 Step 2: Financial Agent Analysis...")
        agent_context.financial_analysis = self._run_financial_agent(agent_context)
        
        # Step 3: Demographic Agent Analysis
        print("\n👥 Step 3: Demographic Agent Analysis...")
        agent_context.demographic_analysis = self._run_demographic_agent(agent_context)
        
        # Step 4: Social Impact Agent Analysis
        print("\n🏛️  Step 4: Social Impact Agent Analysis...")
        agent_context.social_impact = self._run_social_agent(agent_context)
        
        # Step 5: Economic Agent Analysis
        print("\n📊 Step 5: Economic Agent Analysis...")
        agent_context.economic_impact = self._run_economic_agent(agent_context)
        
        # Step 6: Business Agent Analysis
        print("\n🏢 Step 6: Business Agent Analysis...")
        agent_context.business_impact = self._run_business_agent(agent_context)
        
        # Step 7: Risk Agent Analysis
        print("\n⚠️  Step 7: Risk Assessment Agent...")
        agent_context.risk_factors = self._run_risk_agent(agent_context)
        
        # Step 8: Government Coordination
        print("\n🏛️  Step 8: Government Coordination...")
        agent_context.government_coordination = self._run_government_agent(agent_context)
        
        # Step 9: Compile final report
        print("\n📋 Step 9: Compiling Final Report...")
        final_report = self._compile_final_report(agent_context)
        
        return final_report
    
    def _run_financial_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Financial agent analyzes revenue, cost, and economic impact"""
        
        if not self.predictor:
            return {"error": "Predictor not available"}
        
        try:
            # Use RAG context for financial analysis
            financial_data = {
                "policy_type": context.policy_type,
                "context": context.rag_context.get("financial_context", [])
            }
            
            # Predict financial impact
            impact = self.predictor.predict_financial_impact(
                policy_text=context.policy_description,
                historical_context=financial_data.get("context", "")
            )
            
            return {
                "status": "✓ Complete",
                "net_impact": impact.net_impact,
                "estimated_revenue": impact.estimated_revenue_crores,
                "estimated_cost": impact.implementation_cost,
                "per_capita_impact": impact.revenue_per_capita,
                "confidence": impact.confidence_level,
                "assumptions": impact.assumptions
            }
        except Exception as e:
            return {"error": f"Financial analysis failed: {e}"}
    
    def _run_demographic_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Demographic agent analyzes impact on different income classes"""
        
        if not self.predictor:
            return {"error": "Predictor not available"}
        
        try:
            # Predict demographic impact by income class
            demographic_breakdown = []
            main_beneficiaries = []
            main_sufferers = []
            for income_class in ["upper", "middle", "lower_middle", "bpl"]:
                impact = self.predictor.predict_demographic_impact(
                    policy_text=context.policy_description,
                    income_class=income_class,
                )
                demographic_breakdown.append({
                    "income_class": impact.income_class,
                    "beneficiaries": impact.beneficiaries_percent,
                    "sufferers": impact.sufferers_percent,
                    "net_impact_per_person": impact.net_benefit_per_person,
                    "total_affected": impact.population_affected,
                })
                if impact.beneficiaries_percent > impact.sufferers_percent:
                    main_beneficiaries.append(impact.income_class)
                elif impact.sufferers_percent > impact.beneficiaries_percent:
                    main_sufferers.append(impact.income_class)
            
            return {
                "status": "✓ Complete",
                "breakdown": demographic_breakdown,
                "main_beneficiaries": main_beneficiaries,
                "main_sufferers": main_sufferers,
            }
        except Exception as e:
            return {"error": f"Demographic analysis failed: {e}"}
    
    def _run_social_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Social agent analyzes social welfare, education, health impacts"""
        
        try:
            social_context = context.rag_context.get("government_context", [])
            
            # Analyze social aspects from government data
            social_analysis = {
                "status": "✓ Complete",
                "welfare_impact": {
                    "mgnrega_alignment": self._check_alignment(context.policy_description, "MGNREGA"),
                    "education_impact": self._check_impact_area(context.policy_description, ["education", "skill", "training"]),
                    "health_impact": self._check_impact_area(context.policy_description, ["health", "medical", "wellness"])
                },
                "inclusion_metrics": {
                    "scs_coverage": self._estimate_coverage(context.policy_description, "SC/ST"),
                    "minority_coverage": self._estimate_coverage(context.policy_description, "minorities"),
                    "women_empowerment": self._estimate_coverage(context.policy_description, "women")
                },
                "historical_precedents": [p for p in social_context if "outcome" in str(p).lower()][:3]
            }
            
            return social_analysis
        except Exception as e:
            return {"error": f"Social analysis failed: {e}"}
    
    def _run_economic_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Economic agent analyzes GDP, employment, inflation impacts"""
        
        if not self.predictor:
            return {"error": "Predictor not available"}
        
        try:
            # Predict economic impact over 5 years
            impact = self.predictor.project_future_impact(
                policy_text=context.policy_description,
                years=5,
            )
            
            # Format projections
            projections = []
            for projection in impact:
                projections.append({
                    "year": projection.year,
                    "gdp_impact": projection.gdp_impact_percent,
                    "employment_change": projection.employment_jobs_gained,
                    "inflation_impact": projection.inflation_impact,
                    "tax_revenue": projection.tax_revenue_impact_crores,
                })

            avg_gdp_impact = sum(p["gdp_impact"] for p in projections) / len(projections) if projections else 0.0
            if avg_gdp_impact > 0.5:
                long_term_outlook = "Positive"
            elif avg_gdp_impact < -0.5:
                long_term_outlook = "Negative"
            else:
                long_term_outlook = "Stable"
            
            return {
                "status": "✓ Complete",
                "5_year_projections": projections,
                "long_term_outlook": long_term_outlook,
            }
        except Exception as e:
            return {"error": f"Economic analysis failed: {e}"}
    
    def _run_business_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Business agent analyzes industry impact, competitiveness"""
        
        try:
            business_analysis = {
                "status": "✓ Complete",
                "industry_sectors": self._identify_affected_sectors(context.policy_description),
                "compliance_requirements": self._extract_compliance_needs(context.policy_description),
                "competitive_impact": {
                    "small_business_impact": "Medium" if "startup" in context.policy_description.lower() else "Low",
                    "large_corp_impact": "Low" if "msme" in context.policy_description.lower() else "Medium",
                    "sme_focus": "Yes" if any(term in context.policy_description.lower() for term in ["msme", "small", "startup"]) else "No"
                },
                "implementation_timeline": self._estimate_timeline(context.policy_description)
            }
            
            return business_analysis
        except Exception as e:
            return {"error": f"Business analysis failed: {e}"}
    
    def _run_risk_agent(self, context: AgentContext) -> List[str]:
        """Risk agent identifies potential risks and mitigation strategies"""
        
        try:
            risk_factors = []
            
            # Check for known risk patterns
            risk_patterns = {
                "implementation_risk": ["complex", "distributed", "coordination"],
                "compliance_risk": ["mandate", "requirement", "regulation"],
                "economic_risk": ["inflation", "deficit", "unemployment"],
                "social_risk": ["inequality", "disparity", "exclusion"],
                "political_risk": ["controversial", "partisan", "election"]
            }
            
            policy_lower = context.policy_description.lower()
            for risk_type, keywords in risk_patterns.items():
                if any(keyword in policy_lower for keyword in keywords):
                    risk_factors.append(f"⚠️ {risk_type.replace('_', ' ').title()}: Potential issues detected")
            
            # Add RAG-based risk factors
            if context.rag_context.get("economic_context"):
                risk_factors.append("📊 Economic volatility: Current baseline shows market fluctuations")
            
            return risk_factors if risk_factors else ["✓ Low risk profile"]
        except Exception as e:
            return [f"Error: {e}"]
    
    def _run_government_agent(self, context: AgentContext) -> Dict[str, Any]:
        """Government coordination agent identifies stakeholders and alignment"""
        
        try:
            gov_analysis = {
                "status": "✓ Complete",
                "relevant_ministries": self._identify_ministries(context.policy_description),
                "statutory_alignment": {
                    "constitution_articles": self._find_relevant_articles(context.policy_description),
                    "existing_schemes": self._find_related_schemes(context.policy_description),
                    "international_commitments": self._find_sdg_alignment(context.policy_description)
                },
                "stakeholder_mapping": {
                    "primary_stakeholders": self._identify_stakeholders(context.policy_description, "primary"),
                    "secondary_stakeholders": self._identify_stakeholders(context.policy_description, "secondary")
                },
                "rag_references": len(context.rag_context.get("government_context", []))
            }
            
            return gov_analysis
        except Exception as e:
            return {"error": f"Government analysis failed: {e}"}
    
    def _compile_final_report(self, context: AgentContext) -> Dict[str, Any]:
        """Compile all agent outputs into a comprehensive report"""
        
        report = {
            "policy_summary": {
                "description": context.policy_description,
                "type": context.policy_type,
                "rag_context_confidence": bool(context.rag_context.get("financial_context", "").strip())
            },
            "financial_impact": context.financial_analysis,
            "demographic_impact": context.demographic_analysis,
            "social_impact": context.social_impact,
            "economic_outlook": context.economic_impact,
            "business_implications": context.business_impact,
            "risk_assessment": {
                "identified_risks": context.risk_factors or [],
                "overall_risk_level": "Low" if len([r for r in (context.risk_factors or []) if "Error" not in r]) < 3 else "Medium"
            },
            "government_coordination": context.government_coordination,
            "execution_summary": self._generate_execution_summary(context)
        }
        
        print("\n✅ Policy Analysis Complete!")
        return report
    
    def _generate_execution_summary(self, context: AgentContext) -> str:
        """Generate executive summary of analysis"""
        
        summary = f"""
        Policy: {context.policy_type.upper()}
        
        Key Findings:
        • Financial Impact: {context.financial_analysis.get('net_impact') if context.financial_analysis else 'N/A'}
        • Primary Beneficiaries: {', '.join(context.demographic_analysis.get('main_beneficiaries', [])) if context.demographic_analysis else 'N/A'}
        • Economic Projection: {context.economic_impact.get('long_term_outlook', 'N/A') if context.economic_impact else 'N/A'}
        • Risk Level: {'High' if context.risk_factors and len([r for r in context.risk_factors if 'Error' not in r]) > 3 else 'Moderate'}
        """
        
        return summary.strip()

    def _detect_policy_type(self, policy_text: str) -> str:
        """Detect high-level policy category from input text."""
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
        return "general"
    
    # ============ Helper Methods ============
    
    def _check_alignment(self, policy: str, scheme: str) -> bool:
        """Check policy alignment with government scheme"""
        return scheme.lower() in policy.lower()
    
    def _check_impact_area(self, policy: str, keywords: List[str]) -> bool:
        """Check if policy impacts a specific area"""
        policy_lower = policy.lower()
        return any(keyword in policy_lower for keyword in keywords)
    
    def _estimate_coverage(self, policy: str, group: str) -> str:
        """Estimate coverage percentage for a demographic group"""
        if group.lower() in policy.lower() or "all" in policy.lower():
            return "High (70-90%)"
        elif "targeted" in policy.lower():
            return "Medium (40-70%)"
        return "Low (10-40%)"
    
    def _identify_affected_sectors(self, policy: str) -> List[str]:
        """Identify business sectors affected by policy"""
        sector_keywords = {
            "manufacturing": ["manufacturing", "industry", "factory", "production"],
            "agriculture": ["agriculture", "farming", "crop", "kisan"],
            "services": ["services", "logistics", "retail", "trade"],
            "tourism": ["tourism", "hospitality", "travel"],
            "technology": ["technology", "digital", "it", "software"],
            "energy": ["energy", "power", "renewable", "coal"],
            "healthcare": ["health", "medical", "pharma", "hospital"],
            "education": ["education", "skill", "training", "university"]
        }
        
        policy_lower = policy.lower()
        sectors = [sector for sector, keywords in sector_keywords.items() 
                  if any(kw in policy_lower for kw in keywords)]
        
        return sectors if sectors else ["General"]
    
    def _extract_compliance_needs(self, policy: str) -> List[str]:
        """Extract compliance requirements from policy"""
        requirements = []
        
        compliance_patterns = {
            "registration": ["register", "licensed", "certification"],
            "reporting": ["report", "disclosure", "audit"],
            "compliance": ["comply", "adherence", "standard"],
            "documentation": ["document", "filing", "record"]
        }
        
        policy_lower = policy.lower()
        for req_type, keywords in compliance_patterns.items():
            if any(kw in policy_lower for kw in keywords):
                requirements.append(f"✓ {req_type.title()} Requirements")
        
        return requirements if requirements else ["Standard Compliance"]
    
    def _estimate_timeline(self, policy: str) -> str:
        """Estimate implementation timeline"""
        if any(word in policy.lower() for word in ["immediate", "urgent", "emergency"]):
            return "0-3 months"
        elif any(word in policy.lower() for word in ["phase", "gradual", "rolling"]):
            return "6-12 months"
        return "3-6 months"
    
    def _identify_ministries(self, policy: str) -> List[str]:
        """Identify relevant government ministries"""
        ministry_keywords = {
            "Finance": ["tax", "revenue", "budget", "fiscal"],
            "Commerce": ["trade", "export", "import", "commerce"],
            "Labor": ["employment", "wage", "labor", "worker"],
            "Agriculture": ["farmer", "crop", "agriculture", "land"],
            "Health": ["health", "medical", "disease", "nutrition"],
            "Education": ["education", "student", "school", "university"]
        }
        
        policy_lower = policy.lower()
        ministries = [ministry for ministry, keywords in ministry_keywords.items()
                     if any(kw in policy_lower for kw in keywords)]
        
        return ministries if ministries else ["General Administration"]
    
    def _find_relevant_articles(self, policy: str) -> List[str]:
        """Find relevant constitutional articles"""
        return ["Article 14 (Equality)", "Article 21 (Right to Life)", "Article 301 (Trade)"]
    
    def _find_related_schemes(self, policy: str) -> List[str]:
        """Find related government schemes"""
        schemes = []
        scheme_keywords = {
            "MGNREGA": ["employment", "rural", "wage"],
            "PM-JAY": ["health", "insurance", "medical"],
            "PMAY": ["housing", "affordable", "home"],
            "PLI": ["manufacturing", "production", "industry"]
        }
        
        policy_lower = policy.lower()
        for scheme, keywords in scheme_keywords.items():
            if any(kw in policy_lower for kw in keywords):
                schemes.append(scheme)
        
        return schemes if schemes else ["General Scheme"]
    
    def _find_sdg_alignment(self, policy: str) -> List[str]:
        """Find UN Sustainable Development Goals alignment"""
        sdg_keywords = {
            "SDG 1": ["poverty", "welfare", "minimum", "bpl"],
            "SDG 3": ["health", "healthcare", "medical"],
            "SDG 4": ["education", "skill", "training"],
            "SDG 5": ["women", "gender", "equality"],
            "SDG 8": ["employment", "job", "labor"],
            "SDG 10": ["inequality", "disparity", "inclusion"]
        }
        
        policy_lower = policy.lower()
        sdgs = [sdg for sdg, keywords in sdg_keywords.items()
               if any(kw in policy_lower for kw in keywords)]
        
        return sdgs if sdgs else []
    
    def _identify_stakeholders(self, policy: str, stakeholder_type: str) -> List[str]:
        """Identify primary or secondary stakeholders"""
        if stakeholder_type == "primary":
            return ["Government", "Beneficiaries", "Implementing Agencies"]
        return ["Businesses", "NGOs", "International Organizations", "Media"]


# Example usage
if __name__ == "__main__":
    orchestrator = RAGAgentOrchestrator()
    
    # Test policy analysis
    test_policy = """
    Implement a nationwide progressive taxation policy on luxury goods.
    Tax rate increases from 18% to 28% on items priced above ₹10 lakhs.
    Target revenue increase of ₹5000 crore annually.
    Exemptions for essential luxury exports.
    Implementation timeline: 6 months phased rollout.
    """
    
    result = orchestrator.orchestrate_policy_analysis(test_policy)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"Financial Impact: ₹{result['financial_impact'].get('net_impact')} Cr")
    print(f"Risk Level: {result['risk_assessment']['overall_risk_level']}")
    print(f"Stakeholders: {', '.join(result['government_coordination'].get('primary_stakeholders', []))}")
