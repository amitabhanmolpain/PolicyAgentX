from app.models.policy_input import PolicyInput
from graph.policy_graph import graph, initialize_state
from app.models.db_model import policy_collection
from bson import ObjectId
import traceback
import json
from datetime import datetime
import os

# RAG Pipeline (optional, will load if available)
RAG_AVAILABLE = False
try:
    from rag.policy_rag_retriever import analyze_policy_with_rag, PolicyRAGRetriever
    RAG_AVAILABLE = True
except ImportError:
    pass


def make_json_serializable(obj):
    """Convert any object to JSON-serializable format"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return obj


def is_non_india_policy(text: str) -> bool:
    """Check if policy is explicitly for non-India countries"""
    non_india_keywords = [
        "usa", "america", "us", "united states", "american",
        "europe", "european", "uk", "united kingdom", "british",
        "china", "chinese", "japan", "japanese", "south korea", "korean",
        "africa", "african", "australia", "australian", "canada", "canadian",
        "brazil", "mexican", "mexico", "russia", "middle east", "arab",
        "singapore", "thailand", "vietnam", "malaysia"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in non_india_keywords)


def is_india_policy(text: str) -> bool:
    """Check if policy is related to India"""
    india_keywords = [
        "india", "indian", "delhi", "mumbai", "bangalore", "karnataka", 
        "maharashtra", "tamil nadu", "west bengal", "uttar pradesh",
        "delhi ncr", "kolkata", "hyderabad", "pune", "rupee",
        "rupees", "crore", "lakh", "gst", "pib", "ministry", "parliament",
        "lok sabha", "rajya sabha", "indian government", "indian economy",
        "indian rupee", "reserve bank", "rbi", "nifty", "sensex"
    ]
    
    text_lower = text.lower()
    india_mentions = sum(1 for keyword in india_keywords if keyword in text_lower)
    
    # If explicitly non-India, return False
    if is_non_india_policy(text):
        return False
    
    # Default to True (assume India policy unless explicitly non-India)
    return True


# ==============================
# 🔥 MAIN SIMULATION LOGIC
# ==============================
def handle_simulation(data):
    if not data or "text" not in data:
        return {"error": "Policy text is required"}, 400

    try:
        # create policy input - default region to India
        policy = PolicyInput(
            text=data["text"],
            region=data.get("region", "India")
        )

        # Check if policy is explicitly for non-India countries
        if is_non_india_policy(policy.text):
            return {
                "error": "PolicyAgentX is specifically designed for Indian government policies only."
            }, 400

        # Initialize state for graph
        state = initialize_state(policy.text, policy.region)
        
        # run LangGraph pipeline
        result = graph.invoke(state)

        # Extract structured data from agent analyses
        economic_data = result.get("economic_analysis", {})
        social_data = result.get("social_analysis", {})
        business_data = result.get("business_analysis", {})
        government_data = result.get("government_analysis", {})
        risk_data = result.get("risk_analysis", {})
        recommendation_data = result.get("recommendation", {})

        # Build comprehensive response
        final_result = {
            "policy_text": policy.text,
            "region": policy.region,
            "timestamp": datetime.now().isoformat(),
            "economic_impact": str(economic_data.get("economic_analysis", "")),
            "social_impact": str(social_data.get("social_analysis", "")),
            "business_impact": str(business_data.get("business_analysis", "")),
            "government_impact": str(government_data.get("government_analysis", "")),
            "protest_risk": str(risk_data.get("protest_likelihood", "MEDIUM")),
            "affected_groups": str(risk_data.get("affected_groups", "")),
            "public_reaction": str(risk_data.get("public_reaction", "")),
            "risk_confidence": str(risk_data.get("confidence_score", "75%")),
            "explanation": str(recommendation_data.get("recommendation_analysis", "")),
            "recommendation": str(recommendation_data.get("optimized_policy", "")),
        }

        # Make sure all values are JSON-serializable
        final_result = make_json_serializable(final_result)

        # Save to database
        try:
            policy_collection.insert_one(final_result.copy())
        except Exception as db_err:
            print(f"Database save error: {str(db_err)}")

        return final_result, 200
    except Exception as e:
        print(f"Error in handle_simulation: {traceback.format_exc()}")
        return {"error": f"Simulation failed: {str(e)}"}, 500


# ==============================
# 🤖 RAG-ENHANCED SIMULATION (with financial forecasting)
# ==============================
def handle_simulation_with_rag(data):
    """Enhanced simulation using RAG pipeline with:
    - Financial impact prediction
    - Demographic segmentation
    - Future projections
    - Historical policy comparison
    """
    if not data or "text" not in data:
        return {"error": "Policy text is required"}, 400
    
    if not RAG_AVAILABLE:
        return {"error": "RAG pipeline not initialized. Using standard simulation."}, 400
    
    try:
        policy_text = data.get("text", "")
        is_advanced = data.get("advanced_analysis", False)
        
        # Check if India policy
        if is_non_india_policy(policy_text):
            return {
                "error": "PolicyAgentX is specifically designed for Indian government policies only."
            }, 400
        
        print(f"\n🔄 RAG-Enhanced Analysis: {'Advanced' if is_advanced else 'Standard'}")
        
        # Run RAG-enhanced analysis
        rag_result = analyze_policy_with_rag(policy_text)
        analysis = rag_result["analysis"]
        
        # Format for API response
        result = {
            "policy_text": policy_text,
            "analysis_type": "rag_enhanced",
            "timestamp": datetime.now().isoformat(),
            
            # Financial Analysis
            "financial": {
                "net_impact_crores": analysis.financial_impact.net_impact,
                "estimated_revenue_crores": analysis.financial_impact.estimated_revenue_crores,
                "implementation_cost_crores": analysis.financial_impact.implementation_cost,
                "per_capita_impact": f"₹{analysis.financial_impact.revenue_per_capita:,.0f}",
                "confidence": f"{analysis.financial_impact.confidence_level}%",
            },
            
            # Demographic Impact
            "demographic_impact": [
                {
                    "income_class": demo.income_class,
                    "population_affected": demo.population_affected,
                    "beneficiaries_percent": f"{demo.beneficiaries_percent:.1f}%",
                    "sufferers_percent": f"{demo.sufferers_percent:.1f}%",
                    "net_benefit_per_person": f"₹{demo.net_benefit_per_person:,.0f}",
                    "impact": "🟢 BENEFIT" if demo.beneficiaries_percent > demo.sufferers_percent else "🔴 SUFFER"
                }
                for demo in analysis.demographic_impacts
            ],
            
            # Future Outlook
            "future_projections": [
                {
                    "year": proj.year,
                    "gdp_impact": f"{proj.gdp_impact_percent:+.2f}%",
                    "employment_change": f"{proj.employment_jobs_gained:+,} jobs",
                    "inflation_impact": f"{proj.inflation_impact:+.2f}%",
                    "tax_revenue_impact": f"₹{proj.tax_revenue_impact_crores:+,.0f}Cr"
                }
                for proj in analysis.future_projections
            ],
            
            # Summary
            "main_beneficiaries": analysis.main_beneficiaries,
            "main_sufferers": analysis.main_sufferers,
            "risk_factors": analysis.risk_factors,
            "recommendations": analysis.recommendations,
            
            # Full formatted report
            "formatted_report": rag_result["report"]
        }
        
        # Make JSON-serializable
        result = make_json_serializable(result)
        
        # Save to database
        try:
            policy_collection.insert_one(result.copy())
        except Exception as db_err:
            print(f"Database save error: {str(db_err)}")
        
        return result, 200
        
    except Exception as e:
        print(f"Error in RAG analysis: {traceback.format_exc()}")
        return {"error": f"RAG analysis failed: {str(e)}"}, 500


# ==============================
# 📄 PDF HANDLER
# ==============================
def handle_pdf_upload(file):
    if not file:
        return {"error": "No file uploaded"}, 400

    try:
        content = file.read().decode("utf-8", errors="ignore")
        return {"text": content}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# ==============================
# 📜 HISTORY HANDLER
# ==============================
def handle_history():
    try:
        # Query without _id field (already excluded in find)
        data = list(policy_collection.find({}, {"_id": 0}))
        
        # Ensure all data is JSON-serializable
        data = [make_json_serializable(item) for item in data]
        
        return data, 200
    except Exception as e:
        print(f"Error in handle_history: {traceback.format_exc()}")
        return {"error": str(e)}, 500


# ==============================
# ❤️ HEALTH CHECK
# ==============================
def handle_health():
    return {"status": "Backend running 🚀"}, 200


# ==============================
# 🤖 ORCHESTRATED ANALYSIS (RAG + All Agents)
# ==============================
def handle_orchestrated_analysis(data):
    """Comprehensive policy analysis using RAG + AI agents orchestration:
    - Financial Agent: Revenue/cost impact
    - Demographic Agent: Income class effects
    - Social Agent: Welfare & inclusion analysis
    - Economic Agent: GDP & employment predictions
    - Business Agent: Industry competitiveness
    - Risk Agent: Risk factors & mitigation
    - Government Agent: Stakeholder coordination
    """
    if not data or "text" not in data:
        return {"error": "Policy text is required"}, 400
    
    try:
        policy_text = data.get("text", "")
        
        # Check if India policy
        if is_non_india_policy(policy_text):
            return {
                "error": "PolicyAgentX is specifically designed for Indian government policies only."
            }, 400
        
        print(f"\n🔄 Orchestrating Multi-Agent Policy Analysis...")
        
        # Import orchestrator
        from agents.rag_agent_orchestrator import RAGAgentOrchestrator
        
        # Create orchestrator instance
        orchestrator = RAGAgentOrchestrator()
        
        # Run comprehensive analysis
        analysis_result = orchestrator.orchestrate_policy_analysis(policy_text)
        
        # Format response
        result = {
            "policy_text": policy_text,
            "analysis_type": "orchestrated_agents",
            "timestamp": datetime.now().isoformat(),
            
            # Policy Summary
            "policy_summary": analysis_result.get("policy_summary", {}),
            
            # Financial Analysis
            "financial_impact": analysis_result.get("financial_impact", {}),
            
            # Demographic Analysis
            "demographic_impact": analysis_result.get("demographic_impact", {}),
            
            # Social Impact
            "social_impact": analysis_result.get("social_impact", {}),
            
            # Economic Outlook
            "economic_outlook": analysis_result.get("economic_outlook", {}),
            
            # Business Implications
            "business_implications": analysis_result.get("business_implications", {}),
            
            # Risk Assessment
            "risk_assessment": analysis_result.get("risk_assessment", {}),
            
            # Government Coordination
            "government_coordination": analysis_result.get("government_coordination", {}),
            
            # Executive Summary
            "executive_summary": analysis_result.get("execution_summary", "")
        }
        
        # Make JSON-serializable
        result = make_json_serializable(result)
        
        # Save to database
        try:
            policy_collection.insert_one(result.copy())
        except Exception as db_err:
            print(f"Database save error: {str(db_err)}")
        
        return result, 200
        
    except Exception as e:
        print(f"Error in orchestrated analysis: {traceback.format_exc()}")
        return {"error": f"Orchestrated analysis failed: {str(e)}"}, 500