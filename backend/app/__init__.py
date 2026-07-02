from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.routes.chat_routes import chat_bp
from app.routes.policy_routes import policy_bp
from app.routes.upload_routes import upload_bp
from app.services.rag_service import build_rag_service


def create_app() -> Flask:
	load_dotenv()

	backend_dir = Path(__file__).resolve().parents[1]

	app = Flask(__name__)
	app.config.update(
		MAX_CONTENT_LENGTH=50 * 1024 * 1024,
		RAG_DATA_DIR=str(backend_dir / "rag" / "DATA"),
		RAG_CHROMA_DIR=str(backend_dir / "chroma_db" / "rag"),
		RAG_COLLECTION_NAME="policy_rag",
	)

	CORS(
		app,
		resources={
			r"/*": {
				"origins": [
					r"http://localhost:\d+",
					r"http://127\.0\.0\.1:\d+",
				],
				"methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
				"allow_headers": ["Content-Type", "Authorization"],
				"supports_credentials": True,
			}
		},
	)

	app.register_blueprint(policy_bp)
	app.register_blueprint(upload_bp)
	app.register_blueprint(chat_bp)

	app.extensions["rag_service"] = build_rag_service(
		data_dir=app.config["RAG_DATA_DIR"],
		persist_dir=app.config["RAG_CHROMA_DIR"],
		collection_name=app.config["RAG_COLLECTION_NAME"],
	)

	@app.errorhandler(400)
	def handle_bad_request(e):
		return {"error": "Bad request: " + str(e)}, 400

	@app.errorhandler(500)
	def handle_server_error(e):
		return {"error": "Internal server error: " + str(e)}, 500

	return app


app = create_app()
