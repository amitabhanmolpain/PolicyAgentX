from flask import Blueprint, jsonify, request

from app.controllers.upload_controller import handle_reset, handle_upload

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    result, status = handle_upload(file)
    return jsonify(result), status


@upload_bp.route("/reset", methods=["POST"])
def reset():
    result, status = handle_reset()
    return jsonify(result), status
