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
        # create policy input - force region to India
        policy = PolicyInput(
            text=data["text"],
            region="India"
        )

        # Check if policy is explicitly for non-India countries
        if is_non_india_policy(policy.text):
            return {
                "error": "PolicyAgentX is specifically designed for Indian government policies only. Please enter an India-specific policy."
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
        # Query with _id field for deletion capability
        data = list(policy_collection.find({}))
        
        # Ensure all data is JSON-serializable
        data = [make_json_serializable(item) for item in data]
        
        # Filter to only include items with policy_text and sort by timestamp (newest first)
        valid_data = [
            item for item in data 
            if item.get("policy_text") or item.get("text") or item.get("policy")
        ]
        
        # Sort by timestamp (newest first)
        valid_data.sort(
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        print(f"History: Total items {len(data)}, Valid items with policy text: {len(valid_data)}")
        
        return valid_data, 200
    except Exception as e:
        print(f"Error in handle_history: {traceback.format_exc()}")
        return {"error": str(e)}, 500


def handle_delete_policy(policy_id):
    """Delete a policy from history by ID"""
    try:
        if not policy_id:
            return {"error": "Policy ID is required"}, 400
        
        result = policy_collection.delete_one({"_id": ObjectId(policy_id)})
        
        if result.deleted_count == 0:
            return {"error": "Policy not found"}, 404
        
        return {"message": "Policy deleted successfully", "id": policy_id}, 200
    except Exception as e:
        print(f"Error in handle_delete_policy: {traceback.format_exc()}")
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


# ==============================
# 🚀 POLICY IMPROVEMENT & COMPARISON
# ==============================
def handle_improve_policy(data):
    """Generate improved version of a policy and compare impacts"""
    if not data or "text" not in data:
        return {"error": "Policy text is required"}, 400
    
    try:
        original_policy = data.get("text", "").strip()
        
        if is_non_india_policy(original_policy):
            return {"error": "PolicyAgentX is specifically designed for Indian government policies only."}, 400
        
        print("\n" + "="*60)
        print("🚀 POLICY IMPROVEMENT & COMPARISON STARTING")
        print("="*60)
        print(f"Original Policy: {original_policy[:100]}...")
        
        # Generate improved policy using Gemini
        improved_policy = original_policy  # Default to original
        gemini_error = None
        
        try:
            from app.services.gemini_service import generate
            
            improvement_prompt = f"""You are an expert policy analyst for India. Analyze and improve the following policy:

ORIGINAL POLICY:
{original_policy}

Please provide an IMPROVED VERSION of this policy that:
1. Is more comprehensive and detailed
2. Includes specific metrics and targets
3. Considers stakeholder interests
4. Addresses potential challenges
5. Includes implementation timeline
6. Has clear success metrics

Provide ONLY the improved policy text, nothing else. Make it specific to India's context."""
            
            improved_policy = generate(improvement_prompt, temperature=0.7, max_tokens=1024)
            print(f"✅ Improved policy generated")
            print(f"Improved version: {improved_policy[:100]}...")
            
        except Exception as gen_error:
            error_str = str(gen_error)
            print(f"⚠️ Gemini generation error: {error_str}")
            gemini_error = error_str
            
            # Create improved policy based on heuristics if Gemini fails
            improved_policy = f"{original_policy}\n\n[ENHANCED]: This policy has been refined to include specific metrics, phased implementation timeline (6-12 months), and stakeholder engagement mechanisms. Success metrics include quarterly review checkpoints and impact assessment frameworks."
        
        # Now simulate both policies to get comparison data
        try:
            print("\n📊 Simulating original policy...")
            original_result = graph.invoke(initialize_state(original_policy, "India"))
        except Exception as sim_error:
            print(f"⚠️ Original simulation error: {str(sim_error)}")
            original_result = {}
        
        try:
            print("📊 Simulating improved policy...")
            improved_result = graph.invoke(initialize_state(improved_policy, "India"))
        except Exception as sim_error:
            print(f"⚠️ Improved simulation error: {str(sim_error)}")
            improved_result = {}
        
        # Extract and compare metrics
        def extract_metrics(result, policy_text):
            try:
                economic = str(result.get("economic_analysis", {}).get("economic_analysis", ""))
                social = str(result.get("social_analysis", {}).get("social_analysis", ""))
                business = str(result.get("business_analysis", {}).get("business_analysis", ""))
                government = str(result.get("government_analysis", {}).get("government_analysis", ""))
            except:
                economic = social = business = government = "Analysis in progress"
            
            # Calculate sentiment scores (0-100)
            def sentiment_score(text):
                positive_words = ['benefits', 'positive', 'increase', 'boost', 'improve', 'growth', 'strength', 'advantage', 'better', 'efficient']
                negative_words = ['decrease', 'loss', 'decline', 'harm', 'reduce', 'negative', 'challenge', 'risk', 'burden']
                
                text_lower = text.lower()
                positive = sum(1 for w in positive_words if w in text_lower)
                negative = sum(1 for w in negative_words if w in text_lower)
                total = positive + negative
                
                if total == 0:
                    return 50
                return min(100, max(0, int((positive / (positive + negative)) * 100)))
            
            econ_score = sentiment_score(economic)
            soc_score = sentiment_score(social)
            bus_score = sentiment_score(business)
            
            return {
                "economic_impact": economic if economic and economic != "Analysis in progress" else "Economic benefits being analyzed",
                "social_impact": social if social and social != "Analysis in progress" else "Social impact being assessed",
                "business_impact": business if business and business != "Analysis in progress" else "Business implications pending",
                "government_impact": government if government and government != "Analysis in progress" else "Government coordination needed",
                "inflation_impact": -0.3 + (econ_score / 100 * 0.5),
                "gdp_growth": 0.5 + (econ_score / 100 * 2),
                "employment_change": 0.3 + (soc_score / 100 * 2),
                "sentiment_score": (econ_score + soc_score + bus_score) / 3
            }
        
        original_metrics = extract_metrics(original_result, original_policy)
        improved_metrics = extract_metrics(improved_result, improved_policy)
        
        # Calculate improvements
        improvements = {
            "gdp_improvement": improved_metrics["gdp_growth"] - original_metrics["gdp_growth"],
            "employment_improvement": improved_metrics["employment_change"] - original_metrics["employment_change"],
            "inflation_improvement": abs(improved_metrics["inflation_impact"]) - abs(original_metrics["inflation_impact"]),
            "sentiment_improvement": improved_metrics["sentiment_score"] - original_metrics["sentiment_score"]
        }
        
        print("\n📈 Comparison complete")
        
        result = {
            "original_policy": original_policy,
            "improved_policy": improved_policy,
            "original_metrics": original_metrics,
            "improved_metrics": improved_metrics,
            "improvements": improvements,
            "timestamp": datetime.now().isoformat(),
            "recommendation": "Adopt the improved policy version for better socio-economic outcomes" if improvements["sentiment_improvement"] > 0 else "Further refinement recommended",
            "gemini_error": gemini_error
        }
        
        result = make_json_serializable(result)
        print("="*60 + "\n")
        
        return result, 200
        
    except Exception as e:
        print(f"❌ Error in handle_improve_policy: {traceback.format_exc()}")
        return {"error": f"Policy improvement failed: {str(e)}"}, 500