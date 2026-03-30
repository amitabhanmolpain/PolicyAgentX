from flask import Blueprint, request, jsonify
from app.controllers.policy_controllers import (
    handle_simulation,
    handle_pdf_upload,
    handle_history,
    handle_health
)

policy_bp = Blueprint("policy", __name__)


@policy_bp.route("/simulate", methods=["POST"])
def simulate():
    result, status = handle_simulation(request.json)
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


@policy_bp.route("/health", methods=["GET"])
def health():
    result, status = handle_health()
    return jsonify(result), status