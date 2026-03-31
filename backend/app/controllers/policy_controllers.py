from app.models.policy_input import PolicyInput
from graph.policy_graph import graph, initialize_state
from app.models.db_model import policy_collection
from bson import ObjectId
import traceback
import json
from datetime import datetime


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


def is_india_policy(text: str) -> bool:
    """Check if policy is related to India"""
    india_keywords = [
        "india", "indian", "delhi", "mumbai", "bangalore", "karnataka", 
        "maharashtra", "tamil nadu", "west bengal", "uttar pradesh",
        "delhi ncr", "kolkata", "hyderabad", "pune", "delhi", "rupee",
        "rupees", "crore", "lakh", "gst", "pib", "ministry", "parliament",
        "lok sabha", "rajya sabha", "indian government", "indian economy",
        "indian rupee", "reserve bank", "rbi", "nifty", "sensex"
    ]
    
    text_lower = text.lower()
    india_mentions = sum(1 for keyword in india_keywords if keyword in text_lower)
    
    # If 0 India keywords found, it's likely not India policy
    return india_mentions > 0


# ==============================
# 🔥 MAIN SIMULATION LOGIC
# ==============================
def handle_simulation(data):
    if not data or "text" not in data:
        return {"error": "Policy text is required"}, 400

    try:
        # create policy input
        policy = PolicyInput(
            text=data["text"],
            region=data.get("region", "India")
        )

        # Validate India policy
        if not is_india_policy(policy.text):
            return {
                "error": "PolicyAgentX is specifically designed for Indian government policies only. Please provide an Indian policy for analysis."
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