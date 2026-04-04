from app.models.policy_input import PolicyInput
from graph.policy_graph import graph, initialize_state
from app.models.db_model import policy_collection
from bson import ObjectId
import traceback
import json
import re
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


def _simple_stem(word: str) -> str:
    """A lightweight stemmer for consistent keyword matching."""
    token = re.sub(r"[^a-z]", "", word.lower())
    for suffix in ("ingly", "edly", "ment", "tion", "sion", "ance", "ence", "ingly", "edly", "ing", "ed", "ly", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            token = token[:-len(suffix)]
            break
    return token


def _stem_tokens(text: str):
    return [_simple_stem(token) for token in re.findall(r"[a-zA-Z]+", text or "")]


def _has_required_innovation_structure(text: str) -> bool:
    """Check if text has required 'Original:', 'Upgrade:', 'Benefit:' structure"""
    lower = (text or "").lower()
    has_original = "original:" in lower
    has_upgrade = "upgrade:" in lower
    has_benefit = "benefit:" in lower
    has_structure = has_original and has_upgrade and has_benefit
    print(f"  Structure check: Original={has_original}, Upgrade={has_upgrade}, Benefit={has_benefit}, Overall={has_structure}")
    return has_structure


def _build_policy_innovation_fallback(original_policy: str) -> str:
        policy_lower = original_policy.lower()

        def _policy_focus() -> str:
            if any(keyword in policy_lower for keyword in ["tariff", "import", "export", "trade", "customs"]):
                return "Original Policy Focus: A trade or tariff measure that affects imports, domestic prices, and industry competitiveness."
            if any(keyword in policy_lower for keyword in ["subsid", "farmer", "agricultur", "crop", "rural"]):
                return "Original Policy Focus: A support policy for farmers, rural households, or agricultural production."
            if any(keyword in policy_lower for keyword in ["tax", "gst", "income tax", "revenue"]):
                return "Original Policy Focus: A tax, compliance, or revenue policy that changes how money is collected or redistributed."
            if any(keyword in policy_lower for keyword in ["health", "hospital", "medicine", "clinic"]):
                return "Original Policy Focus: A health policy that changes access, affordability, or service delivery."
            if any(keyword in policy_lower for keyword in ["education", "school", "college", "student", "skill"]):
                return "Original Policy Focus: An education or skill-building policy that changes access and outcomes."
            if any(keyword in policy_lower for keyword in ["housing", "rent", "home", "shelter"]):
                return "Original Policy Focus: A housing policy that changes affordability and access to shelter."
            if any(keyword in policy_lower for keyword in ["energy", "power", "electric", "renewable"]):
                return "Original Policy Focus: An energy policy that changes prices, access, or sustainability."
            return "Original Policy Focus: A general public policy that needs sharper targeting, clearer execution, and measurable outcomes."

        def _policy_name() -> str:
            if any(keyword in policy_lower for keyword in ["tariff", "import", "export", "trade", "customs"]):
                return "Competitiveness-First Trade Shield"
            if any(keyword in policy_lower for keyword in ["subsid", "farmer", "agricultur", "crop", "rural"]):
                return "Precision Rural Support Grid"
            if any(keyword in policy_lower for keyword in ["tax", "gst", "income tax", "revenue"]):
                return "Smart Compliance and Relief Engine"
            if any(keyword in policy_lower for keyword in ["health", "hospital", "medicine", "clinic"]):
                return "Targeted Health Access Accelerator"
            if any(keyword in policy_lower for keyword in ["education", "school", "college", "student", "skill"]):
                return "Outcome-Led Learning Upgrade"
            if any(keyword in policy_lower for keyword in ["housing", "rent", "home", "shelter"]):
                return "Affordable Housing Access Platform"
            if any(keyword in policy_lower for keyword in ["energy", "power", "electric", "renewable"]):
                return "Grid Efficiency and Energy Relief Plan"
            return "Strategic Policy Upgrade"

        def _innovation_blocks() -> str:
            if any(keyword in policy_lower for keyword in ["tariff", "import", "export", "trade", "customs"]):
                return f"""- Original: {original_policy}
    Upgrade: Replace a blunt tariff with a tiered trade framework that protects essential goods, applies higher rates to non-essential luxury imports, and gives relief to critical industrial inputs.
    Benefit: Domestic industry gets protection without creating avoidable price shocks for consumers or manufacturers.
- Original: A single tariff rule for all imports.
    Upgrade: Add automatic exemption checks for medicines, raw materials, and export-linked sectors, with monthly review triggers based on inflation and supply shortages.
    Benefit: The policy becomes more precise and avoids hurting sectors that need imported inputs.
- Original: Manual enforcement and static rates.
    Upgrade: Use customs analytics, sector dashboards, and phased rollout to detect leakage, route violations, and update rates when market conditions change.
    Benefit: Better compliance, less smuggling, and faster correction when the policy overshoots.
"""

            if any(keyword in policy_lower for keyword in ["subsid", "farmer", "agricultur", "crop", "rural"]):
                return f"""- Original: {original_policy}
    Upgrade: Replace blanket subsidy delivery with direct benefit transfer linked to verified land records, crop stage, and local distress signals.
    Benefit: Stops leakage and sends support to the intended farmers faster.
- Original: Flat support for everyone.
    Upgrade: Scale assistance by crop type, rainfall stress, market price shock, and farm size so vulnerable households receive more when risk is highest.
    Benefit: Better targeting improves fairness and impact.
- Original: Manual approval and slow payout.
    Upgrade: Add digital eligibility checks, auto-approval for verified cases, and a grievance dashboard for local officers.
    Benefit: Faster disbursement and higher public trust.
"""

            if any(keyword in policy_lower for keyword in ["tax", "gst", "income tax", "revenue"]):
                return f"""- Original: {original_policy}
    Upgrade: Convert the policy into a targeted compliance system with relief for honest small taxpayers and stronger checks for high-risk evasion.
    Benefit: Better revenue collection without punishing low-risk households.
- Original: One-size-fits-all enforcement.
    Upgrade: Use income bands, sector risk scores, and transaction patterns to customize enforcement and relief.
    Benefit: The policy becomes fairer and causes less economic friction.
- Original: Slow manual processing.
    Upgrade: Add live dashboards, automated notices, and quarterly policy reviews for administrators.
    Benefit: Faster implementation and fewer administrative bottlenecks.
"""

            if any(keyword in policy_lower for keyword in ["health", "hospital", "medicine", "clinic"]):
                return f"""- Original: {original_policy}
    Upgrade: Shift from a broad health push to targeted service delivery using verified patient groups, local facility mapping, and priority coverage for high-risk districts.
    Benefit: Better access for the people who need care most.
- Original: Generic access improvement.
    Upgrade: Add appointment routing, medicine stock tracking, and outcome monitoring at district level.
    Benefit: Less waiting, fewer shortages, and stronger service quality.
- Original: Manual execution.
    Upgrade: Use a digital health control room with alerts for delays, shortages, and underperforming facilities.
    Benefit: Faster correction and better accountability.
"""

            if any(keyword in policy_lower for keyword in ["education", "school", "college", "student", "skill"]):
                return f"""- Original: {original_policy}
    Upgrade: Redesign the policy around targeted learning outcomes, student support, and local skill pathways instead of a broad funding promise.
    Benefit: More of the budget reaches actual learning improvement.
- Original: Uniform support for all institutions.
    Upgrade: Tie funding to attendance, learning gains, and local labor demand so resources flow to the best-performing programs.
    Benefit: Higher quality and better job relevance.
- Original: Slow monitoring.
    Upgrade: Add outcome dashboards for schools and districts with quarterly review cycles.
    Benefit: Problems are caught earlier and fixed faster.
"""

            if any(keyword in policy_lower for keyword in ["housing", "rent", "home", "shelter"]):
                return f"""- Original: {original_policy}
    Upgrade: Turn the idea into a targeted housing access program with verified beneficiary lists, location-based rent support, and phased construction support.
    Benefit: Support reaches families under the highest housing pressure.
- Original: Broad housing help.
    Upgrade: Prioritize low-income households, migrant workers, and high-rent urban zones using local affordability data.
    Benefit: The policy becomes more equitable and cost-effective.
- Original: Slow rollout.
    Upgrade: Add a digital allocation dashboard and quarterly market review to adjust subsidies and supply targets.
    Benefit: Better pace and less waste.
"""

            if any(keyword in policy_lower for keyword in ["energy", "power", "electric", "renewable"]):
                return f"""- Original: {original_policy}
    Upgrade: Redesign the policy around targeted power relief, grid efficiency, and support for cleaner generation instead of a broad subsidy.
    Benefit: Lower power waste and more reliable supply.
- Original: Static support across users.
    Upgrade: Use usage bands, peak demand data, and outage signals to direct support where stress is highest.
    Benefit: Better system stability and fairer pricing.
- Original: Manual monitoring.
    Upgrade: Add a live grid dashboard and automated alerts for loss, overload, and regional shortages.
    Benefit: Faster response and lower technical losses.
"""

            return f"""- Original: {original_policy}
    Upgrade: Make the policy targeted, measurable, and tied to verified outcomes instead of using a broad one-size-fits-all rollout.
    Benefit: Less leakage, better execution, and stronger results for the intended group.
- Original: Broad support without precision.
    Upgrade: Add real-time monitoring, local verification, and dynamic benefit scaling based on need and performance.
    Benefit: Public money is used more efficiently and trust improves.
- Original: Manual implementation path.
    Upgrade: Use a digital control room and a quarterly review cycle to correct failures quickly.
    Benefit: Faster corrections, stronger accountability, and better long-term impact.
"""

        return f"""Policy Name: {_policy_name()}

{_policy_focus()}

Innovation Deltas From Original:
{_innovation_blocks()}

Execution Blueprint:
- Phase 1 (0-6 months): Define eligibility rules, build the digital workflow, and pilot the policy in high-need districts or sectors.
- Phase 2 (6-18 months): Scale nationally, monitor outcomes monthly, and tighten rules based on real performance data.

Expected Measurable Outcomes:
- GDP impact: Moderate positive uplift from better targeting and lower leakage.
- Employment impact: Higher stability in the affected sector and stronger local confidence.
- Inflation impact: Controlled risk through phased rollout and exemption logic.

Tech/AI Edge:
- Automated eligibility and verification engine.
- Live dashboard for monitoring leakage, delays, and outcome drift.
"""


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
            "rag_source": str(result.get("rag_source", "")),
            "rag_context": str(result.get("rag_context", "")),
            "historical_protest_cases": result.get("historical_protest_cases", []),
            "economic_impact": str(economic_data.get("economic_analysis", "")),
            "social_impact": str(social_data.get("social_analysis", "")),
            "business_impact": str(business_data.get("business_analysis", "")),
            "government_impact": str(government_data.get("government_analysis", "")),
            "protest_risk": str(risk_data.get("protest_likelihood", "MEDIUM")),
            "protest_risk_score": int(risk_data.get("protest_risk_score", result.get("protest_risk_score", 5))),
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
            from app.services.gemini_service import generate, is_error_response
            
            improvement_prompt = f"""
You are a bold, visionary Indian policy architect.

Original policy idea:
"{original_policy}"

Task:
Create a UNIQUE improved policy that is clearly built from the original idea, but significantly better.

Hard rules:
1) Do NOT write generic explanations like "what this policy means".
2) Do NOT criticize vaguely. Show exact upgrades over the original.
3) Every innovation must be specific, implementable, and measurable.
4) Use plain text only. No markdown symbols.
5) Think like a decisive policymaker: propose one strong mechanism that changes how the policy actually works.
6) If the original policy is about subsidies, benefits, welfare, tax, farmers, or households, upgrade it with direct targeting, live verification, automation, and leakage prevention.
7) Avoid filler language. Every bullet must change the policy design in a meaningful way.

Output format (strict):
Policy Name: <short memorable name>

Innovation Deltas From Original:
- Original: <what original policy did>
    Upgrade: <what you changed>
    Benefit: <economic/social/government benefit in one line>
- Original: ...
    Upgrade: ...
    Benefit: ...
- Original: ...
    Upgrade: ...
    Benefit: ...

Execution Blueprint:
- Phase 1 (0-6 months): <owners, actions, enforcement>
- Phase 2 (6-18 months): <scale-up, tech systems, course correction>

Expected Measurable Outcomes:
- GDP impact: <range or estimate>
- Employment impact: <range or estimate>
- Inflation impact: <range or estimate>

Tech/AI Edge:
- <1-2 concrete digital or AI mechanisms that make this policy superior>
"""
            
            improved_policy = generate(improvement_prompt, temperature=0.7, max_tokens=1024)
            if is_error_response(improved_policy):
                raise RuntimeError(improved_policy["error"])
            
            if not _has_required_innovation_structure(improved_policy):
                print(f"⚠️ Model output missing required structure, using fallback instead")
                gemini_error = "Model output format incorrect; using fallback"
                improved_policy = _build_policy_innovation_fallback(original_policy)
            else:
                print(f"✅ Improved policy generated with correct structure")
                print(f"Improved version: {improved_policy[:100]}...")
            
        except Exception as gen_error:
            error_str = str(gen_error)
            print(f"⚠️ Gemini generation error: {error_str}")
            gemini_error = error_str
            
            # Create improved policy based on heuristics if Gemini fails
            improved_policy = _build_policy_innovation_fallback(original_policy)
        
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

                stems = _stem_tokens(text)
                if not stems:
                    return 50

                positive_stems = {_simple_stem(word) for word in positive_words}
                negative_stems = {_simple_stem(word) for word in negative_words}

                positive = sum(1 for stem in stems if stem in positive_stems)
                negative = sum(1 for stem in stems if stem in negative_stems)
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
                "rag_context": str(result.get("rag_context", "")),
                "historical_protest_cases": result.get("historical_protest_cases", []),
                "protest_risk_score": int(result.get("risk_analysis", {}).get("protest_risk_score", result.get("protest_risk_score", 5))),
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