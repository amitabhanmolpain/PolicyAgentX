from flask import Blueprint, request, jsonify
from app.controllers.policy_controllers import (
    handle_simulation,
    handle_simulation_with_rag,
    handle_pdf_upload,
    handle_history,
    handle_health,
    handle_orchestrated_analysis,
    handle_delete_policy,
    handle_improve_policy
)

policy_bp = Blueprint("policy", __name__)


@policy_bp.route("/simulate", methods=["POST"])
def simulate():
    result, status = handle_simulation(request.json)
    return jsonify(result), status


@policy_bp.route("/simulate-advanced", methods=["POST"])
def simulate_advanced():
    """RAG-enhanced simulation with:
    - Financial forecasting
    - Demographic segmentation
    - Future projections
    - Historical comparison
    """
    result, status = handle_simulation_with_rag(request.json)
    return jsonify(result), status


@policy_bp.route("/analyze-with-agents", methods=["POST"])
def analyze_with_agents():
    """Orchestrated analysis using RAG + all AI agents:
    - Financial Agent: Revenue/cost analysis
    - Demographic Agent: Income class impact
    - Social Agent: Welfare & inclusion
    - Economic Agent: GDP & employment predictions
    - Business Agent: Industry impact
    - Risk Agent: Risk assessment
    - Government Agent: Stakeholder coordination
    """
    result, status = handle_orchestrated_analysis(request.json)
    return jsonify(result), status


@policy_bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    result, status = handle_pdf_upload(file)
    return jsonify(result), status


@policy_bp.route("/history", methods=["GET"])
def history():
    result, status = handle_history()
    return jsonify(result), status


@policy_bp.route("/history/<policy_id>", methods=["DELETE"])
def delete_policy(policy_id):
    result, status = handle_delete_policy(policy_id)
    return jsonify(result), status


@policy_bp.route("/improve", methods=["POST"])
def improve():
    """Generate an improved version of a policy and compare impacts"""
    result, status = handle_improve_policy(request.json)
    return jsonify(result), status


@policy_bp.route("/health", methods=["GET"])
def health():
    result, status = handle_health()
    return jsonify(result), status