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

ORCHESTRATOR_AVAILABLE = False
try:
    from agents.rag_orchestrator import RAGEnhancedOrchestratorAgent
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    pass


def _default_frontend_sections(policy_text: str) -> dict:
    """Fallback structure for 7-section frontend cards when model output is partial."""
    text = (policy_text or "").lower()

    amount_match = re.search(r"(?:rs\.?|rupee|rupees)\s*([\d,]+(?:\.\d+)?)", text)
    monthly_amount = float(amount_match.group(1).replace(",", "")) if amount_match else 1000.0

    if any(k in text for k in ["farmer", "agri", "kisan", "rural"]):
        base_population = 110_000_000
    elif any(k in text for k in ["immigrant", "migrant", "migration"]):
        base_population = 65_000_000
    elif any(k in text for k in ["student", "education", "school", "college"]):
        base_population = 260_000_000
    elif any(k in text for k in ["health", "hospital", "insurance"]):
        base_population = 400_000_000
    else:
        base_population = 150_000_000

    coverage = 0.28 if any(k in text for k in ["low income", "target", "poor", "backward"]) else 0.2
    people_count = int(base_population * coverage)
    annual_spend = people_count * monthly_amount * 12.0

    def fmt_people(n: int) -> str:
        if n >= 10_000_000:
            return f"{round(n / 10_000_000, 2)} crore people (~{n:,})"
        if n >= 100_000:
            return f"{round(n / 100_000, 2)} lakh people (~{n:,})"
        return f"{n:,} people"

    def fmt_inr(amount: float) -> str:
        if amount >= 10_000_000:
            return f"{round(amount / 10_000_000, 2)} crores"
        if amount >= 100_000:
            return f"{round(amount / 100_000, 2)} lakhs"
        return f"{round(amount, 2)} rupees"

    return {
        "policy_summary": {
            "simple_meaning": policy_text[:220] if policy_text else "Policy analysis summary unavailable",
            "issuing_ministry": "To be determined",
            "implementation_timeline": "Phased rollout recommended",
            "total_people_impacted_india": fmt_people(people_count),
            "confidence_score": 35,
        },
        "affected_groups": {
            "groups": [
                {
                    "group_name": "Poor / Below Poverty Line",
                    "population_impact_percent": "N/A",
                    "status": "BENEFITED",
                    "reason": "Pending deeper model evidence",
                },
            ],
            "confidence_score": 35,
        },
        "economic_impact": {
            "gdp_impact_percent": "N/A",
            "revenue_generated_inr_crores": "N/A",
            "required_public_spend_inr": fmt_inr(annual_spend),
            "tax_collection_impact": "N/A",
            "employment_impact_jobs": "N/A",
            "inflation_risk": "Medium",
            "fiscal_deficit_impact": "N/A",
            "confidence_score": 35,
        },
        "timeline": {
            "year_1": {"immediate_effect": "Initial rollout", "adoption_or_growth": "25-40%", "inr_crore_estimate": f"SPEND {fmt_inr(annual_spend * 0.55)}"},
            "year_2_3": {"immediate_effect": "Scale-up phase", "adoption_or_growth": "45-65%", "inr_crore_estimate": f"SPEND {fmt_inr(annual_spend * 1.35)}"},
            "year_5": {"immediate_effect": "Stabilization", "adoption_or_growth": "65-82%", "inr_crore_estimate": f"GENERATE {fmt_inr(annual_spend * 0.85)}"},
            "year_10": {"immediate_effect": "Mature impact", "adoption_or_growth": "80-92%", "inr_crore_estimate": f"GENERATE {fmt_inr(annual_spend * 1.35)}"},
            "confidence_score": 35,
        },
        "global_impact": {
            "india_global_position": "N/A",
            "fdi_impact": "N/A",
            "trade_balance_impact": "N/A",
            "comparison_usa_china_eu": "N/A",
            "world_bank_imf_reaction": "N/A",
            "competitiveness_score_change": "N/A",
            "confidence_score": 35,
        },
        "protest_risk": {
            "risk_score_1_to_10": 5,
            "likely_protesting_groups": [],
            "high_risk_states_cities": [],
            "historical_similar_protests": [],
            "confidence_score": 35,
        },
        "improvements": {
            "three_bold_improvements": [
                "Use targeted eligibility and direct delivery",
                "Adopt phased rollout with monthly monitoring",
                "Add protections for vulnerable communities",
            ],
            "lower_protest_risk_modified_version": "Pilot-first implementation with grievance redressal",
            "phased_rollout_recommendation": "Pilot 6 months, scale 18 months",
            "confidence_score": 35,
        },
    }


def _merge_frontend_sections(generated: dict, fallback: dict) -> dict:
    """Ensure all 7 sections exist with confidence scores and safe defaults."""
    merged = {}
    for section_key, fallback_value in fallback.items():
        section_value = generated.get(section_key) if isinstance(generated, dict) else None
        if isinstance(section_value, dict):
            merged_section = fallback_value.copy()
            merged_section.update(section_value)
            if "confidence_score" not in merged_section:
                merged_section["confidence_score"] = fallback_value.get("confidence_score", 35)
            merged[section_key] = merged_section
        else:
            merged[section_key] = fallback_value
    return merged


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


def _parse_json_block(text: str) -> dict:
    """Parse first valid JSON object from model output."""
    if not text:
        return {}
    candidate = text.strip()
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(candidate[start:end + 1])
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _midpoint_from_text(value: str, default: float = 0.0) -> float:
    """Extract midpoint from numeric strings like '1-3%', '+2.5%', '5000-9000'."""
    if not value:
        return default
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", str(value))
    if not nums:
        return default
    if len(nums) == 1:
        try:
            return float(nums[0])
        except Exception:
            return default
    try:
        return (float(nums[0]) + float(nums[1])) / 2.0
    except Exception:
        return default


def _extract_metrics_from_simulation_result(sim_result: dict) -> dict:
    """Extract compare metrics from simulation output without hardcoded display strings."""
    cards = (sim_result or {}).get("frontend_cards", {}) if isinstance(sim_result, dict) else {}
    econ = cards.get("economic_impact", {}) if isinstance(cards, dict) else {}

    gdp_growth = _midpoint_from_text(str(econ.get("gdp_impact_percent", "0")), 0.0)
    inflation_label = str(econ.get("inflation_risk", "Medium")).lower()
    inflation_impact = 2.8 if "high" in inflation_label else (1.6 if "medium" in inflation_label else 0.8)

    employment_text = str(econ.get("employment_impact_jobs", ""))
    employment_change = _midpoint_from_text(employment_text, 0.5)
    if abs(employment_change) > 1000:
        # Convert large absolute job counts into a bounded relative score for graph compatibility.
        employment_change = max(-8.0, min(8.0, employment_change / 100000.0))

    protest_score = 5
    try:
        protest_score = int(cards.get("protest_risk", {}).get("risk_score_1_to_10", sim_result.get("protest_risk_score", 5)))
    except Exception:
        protest_score = 5
    sentiment_score = max(0.0, min(100.0, 100.0 - (protest_score * 8.5)))

    return {
        "economic_impact": str((sim_result or {}).get("economic_impact", "")),
        "social_impact": str((sim_result or {}).get("social_impact", "")),
        "business_impact": str((sim_result or {}).get("business_impact", "")),
        "government_impact": str((sim_result or {}).get("government_impact", "")),
        "rag_context": str((sim_result or {}).get("rag_context", "")),
        "historical_protest_cases": (sim_result or {}).get("historical_protest_cases", []),
        "protest_risk_score": protest_score,
        "inflation_impact": float(inflation_impact),
        "gdp_growth": float(gdp_growth),
        "employment_change": float(employment_change),
        "sentiment_score": float(sentiment_score),
        "revenue_generated_inr_crores": str(econ.get("revenue_generated_inr_crores", "")),
    }


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

        # Run baseline LangGraph pipeline
        result = graph.invoke(state)

        # Run deep structured orchestrator for 7-section JSON cards
        fallback_sections = _default_frontend_sections(policy.text)
        frontend_cards = fallback_sections
        orchestrator_error = None

        if ORCHESTRATOR_AVAILABLE:
            try:
                orchestrator = RAGEnhancedOrchestratorAgent()
                orchestration_result = orchestrator.analyze_policy(policy.text, policy.region)
                generated_cards = orchestration_result.get("frontend_cards", {})
                frontend_cards = _merge_frontend_sections(generated_cards, fallback_sections)

                # Merge key risk values into baseline result if present
                if isinstance(orchestration_result.get("risk_analysis"), dict):
                    result["risk_analysis"] = {
                        **(result.get("risk_analysis") or {}),
                        **orchestration_result.get("risk_analysis", {}),
                    }
            except Exception as orchestrator_exc:
                orchestrator_error = str(orchestrator_exc)
                frontend_cards = fallback_sections

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
            "frontend_cards": frontend_cards,
            "policy_summary": frontend_cards.get("policy_summary", {}),
            "affected_groups_section": frontend_cards.get("affected_groups", {}),
            "economic_impact_section": frontend_cards.get("economic_impact", {}),
            "timeline": frontend_cards.get("timeline", {}),
            "global_impact": frontend_cards.get("global_impact", {}),
            "protest_risk_section": frontend_cards.get("protest_risk", {}),
            "improvements": frontend_cards.get("improvements", {}),
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

        if orchestrator_error:
            final_result["orchestrator_error"] = orchestrator_error

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
        
        # Generate improved policy + compare-ready innovation blocks using strict JSON
        improved_policy = original_policy
        improved_policy_name = "Improved Policy"
        innovation_blocks = []
        improved_policy_points = []
        original_cons = []
        gemini_error = None

        try:
            from app.services.gemini_service import generate, is_error_response

            improvement_prompt = f"""
You are India's best policy economist and architect. Think DEEPLY about real constraints, tradeoffs, and unintended consequences.

ORIGINAL POLICY:
{original_policy}

YOUR TASK:
1. Identify concrete structural weaknesses (not vague criticisms)
2. Propose measurable, implementable improvements with numbers and mechanisms
3. Consider fiscal sustainability, social impact, behavioral responses
4. Address real barriers: administrative capacity, political feasibility, implementation systems

Return VALID JSON ONLY (no markdown, no code blocks, no explanation outside JSON):
{{
  "policy_name": "specific memorable name",
  "improved_policy_text": "Full detailed improved policy (8-15 sentences). Must include: WHO exactly benefits, HOW much in rupees/day/month, WHEN each phase, WHAT enforcement/verification mechanisms, WHY this addresses original's gaps, HOW it avoids original's pitfalls.",
  "innovation_blocks": [
    {{"original_gap": "concrete weakness from original", "upgrade": "specific solution with implementation details", "why_it_wins": "quantified benefit with measurable impact"}},
    {{"original_gap": "...", "upgrade": "...", "why_it_wins": "..."}},
    {{"original_gap": "...", "upgrade": "...", "why_it_wins": "..."}}
  ],
  "improved_policy_points": ["substantive advantage 1 with specifics", "substantive advantage 2 with specifics", "substantive advantage 3 with specifics", "substantive advantage 4 with specifics"],
  "original_policy_cons": ["real fiscal/social risk 1: explain downside", "real fiscal/social risk 2: explain downside", "real fiscal/social risk 3: explain downside", "real fiscal/social risk 4: explain downside"]
}}

REAL CON EXAMPLES (for a farmer pension of rupees 3000/month):
- "Fiscal burden: 3000/month × 15 crore small farmers × 12 = 54,000 crore annually; this diverts funds from irrigation/electricity/schools"
- "Inflation risk: Increasing rural purchasing power without corresponding supply increase could push food prices up 4-7%, harming urban poor and city workers"
- "Opportunity cost: This 54,000 crore/year could alternatively fund: 100,000 irrigation wells, rural electrification for 500 districts, or 50,000 primary schools"
- "Moral hazard: Unconditional cash without productivity conditions may reduce farmers' incentive to adopt better cultivation practices, irrigation tech, or value-added processing"
- "Taxpayer perception: Lower-middle class taxpayers (IT, services, small business) who earn 30-50k/month may resist subsidizing farmers earning same; political backlash risk"
- "Administrative leakage: Verifying eligibility (landholding, income, farming status) across villages requires systems 60% of states lack; expect 15-30% fraud/duplication"
- "Dependency trap: Unconditional support for 20+ years without skill development or technology adoption may leave farmers unprepared for climate shocks, market shifts, or generational transition"

Be intellectually rigorous. Show you understand real tradeoffs, fiscal algebra, and behavioral economics.
"""

            improved_json_text = generate(improvement_prompt, temperature=0.45, max_tokens=1400)
            if is_error_response(improved_json_text):
                raise RuntimeError(improved_json_text["error"])

            first_text = str(improved_json_text).replace("```json", "").replace("```", "").strip()
            parsed = _parse_json_block(first_text)
            candidate_policy = str(parsed.get("improved_policy_text", "")).strip()

            if len(candidate_policy) < 40:
                retry_prompt = (
                    "Your previous output was not parseable JSON. "
                    "Return ONLY valid JSON with the exact same schema and no markdown fences."
                    f"\n\nOriginal policy:\n{original_policy}"
                )
                retry_text = generate(retry_prompt, temperature=0.2, max_tokens=1400)
                if not is_error_response(retry_text):
                    second_text = str(retry_text).replace("```json", "").replace("```", "").strip()
                    retry_parsed = _parse_json_block(second_text)
                    if isinstance(retry_parsed, dict) and retry_parsed.get("improved_policy_text"):
                        parsed = retry_parsed
                        candidate_policy = str(parsed.get("improved_policy_text", "")).strip()

            if len(candidate_policy) < 40:
                raise RuntimeError("Improved policy JSON missing improved_policy_text")

            improved_policy = candidate_policy
            improved_policy_name = str(parsed.get("policy_name", "Improved Policy")).strip() or "Improved Policy"
            innovation_blocks = parsed.get("innovation_blocks", []) if isinstance(parsed.get("innovation_blocks"), list) else []
            improved_policy_points = parsed.get("improved_policy_points", []) if isinstance(parsed.get("improved_policy_points"), list) else []
            original_cons = parsed.get("original_policy_cons", []) if isinstance(parsed.get("original_policy_cons"), list) else []

            print("✅ Improved policy JSON generated")
            print(f"Improved version: {improved_policy[:120]}...")

        except Exception as gen_error:
            error_str = str(gen_error)
            print(f"⚠️ Gemini generation error: {error_str}")
            gemini_error = error_str
            improved_policy = _build_policy_innovation_fallback(original_policy)
        
        # Simulate both policies using the same /simulate logic used by frontend.
        try:
            print("\n📊 Simulating original policy...")
            original_result, original_status = handle_simulation({"text": original_policy, "region": "India"})
            if original_status != 200:
                raise RuntimeError(str(original_result.get("error", "Original simulation failed")))
        except Exception as sim_error:
            print(f"⚠️ Original simulation error: {str(sim_error)}")
            original_result = {}

        try:
            print("📊 Simulating improved policy...")
            improved_result, improved_status = handle_simulation({"text": improved_policy, "region": "India"})
            if improved_status != 200:
                raise RuntimeError(str(improved_result.get("error", "Improved simulation failed")))
        except Exception as sim_error:
            print(f"⚠️ Improved simulation error: {str(sim_error)}")
            improved_result = {}

        original_metrics = _extract_metrics_from_simulation_result(original_result)
        improved_metrics = _extract_metrics_from_simulation_result(improved_result)

        # Build AI compare intelligence so frontend is not forced to synthesize hardcoded text.
        compare_intelligence = {}
        try:
            from app.services.gemini_service import generate, is_error_response

            intelligence_prompt = f"""
You are a senior Indian policy economist and evaluator with deep domain expertise.

ORIGINAL POLICY:
{original_policy}

IMPROVED POLICY:
{improved_policy}

Original simulation:
{json.dumps((original_result or {}).get('frontend_cards', {}), ensure_ascii=False)[:6000]}

Improved simulation:
{json.dumps((improved_result or {}).get('frontend_cards', {}), ensure_ascii=False)[:6000]}

Return VALID JSON ONLY (no markdown, no code blocks):
{{
  "innovation_blocks": [
    {{"original_gap": "realistic weakness", "upgrade": "concrete improvement", "why_it_wins": "specific measurable benefit"}},
    {{"original_gap": "...", "upgrade": "...", "why_it_wins": "..."}},
    {{"original_gap": "...", "upgrade": "...", "why_it_wins": "..."}}
  ],
  "improved_policy_points": ["substantive pro 1", "substantive pro 2", "substantive pro 3", "substantive pro 4", "substantive pro 5"],
  "original_policy_cons": ["fiscal/social risk 1: specific impact", "fiscal/social risk 2: specific impact", "fiscal/social risk 3: specific impact", "fiscal/social risk 4: specific impact"],
  "original_summary": "honest assessment of original (include limitations)",
  "improved_summary": "how improved version addresses those limitations"
}}

CRITICAL ANALYSIS GUIDANCE:
For agriculture/farm subsidies:
- Fiscal cost per beneficiary per year
- Inflation risk on food prices
- Urban income class perception
- Tax burden on high earners
- Administrative overhead

Be intellectually rigorous. Identify REAL tradeoffs, not generic improvements.
"""

            intelligence_text = generate(intelligence_prompt, temperature=0.35, max_tokens=1200)
            if not is_error_response(intelligence_text):
                compare_intelligence = _parse_json_block(str(intelligence_text))
        except Exception as intelligence_error:
            print(f"⚠️ Compare intelligence generation failed: {str(intelligence_error)}")

        if not isinstance(compare_intelligence, dict):
            compare_intelligence = {}

        if not compare_intelligence.get("innovation_blocks") and innovation_blocks:
            compare_intelligence["innovation_blocks"] = innovation_blocks
        if not compare_intelligence.get("improved_policy_points") and improved_policy_points:
            compare_intelligence["improved_policy_points"] = improved_policy_points
        if not compare_intelligence.get("original_policy_cons") and original_cons:
            compare_intelligence["original_policy_cons"] = original_cons
        if not compare_intelligence.get("original_summary"):
            compare_intelligence["original_summary"] = str(original_metrics.get("economic_impact", "")).strip()[:260]
        if not compare_intelligence.get("improved_summary"):
            compare_intelligence["improved_summary"] = str(improved_metrics.get("economic_impact", "")).strip()[:260]
        
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
            "improved_policy_name": improved_policy_name,
            "improved_policy": improved_policy,
            "original_metrics": original_metrics,
            "improved_metrics": improved_metrics,
            "improvements": improvements,
            "innovation_blocks": compare_intelligence.get("innovation_blocks", []),
            "improved_policy_points": compare_intelligence.get("improved_policy_points", []),
            "original_policy_cons": compare_intelligence.get("original_policy_cons", []),
            "original_summary": compare_intelligence.get("original_summary", ""),
            "improved_summary": compare_intelligence.get("improved_summary", ""),
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