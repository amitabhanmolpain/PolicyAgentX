from flask import Blueprint, jsonify, request

from app.controllers.chat_controller import handle_chat

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    result, status = handle_chat(request.get_json(silent=True) or {})
    return jsonify(result), status
