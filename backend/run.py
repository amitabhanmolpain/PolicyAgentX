from flask import Flask
from flask_cors import CORS
from app.routes.policy_routes import policy_bp
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure CORS to allow requests from frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            r"http://localhost:\\d+",
            r"http://127\.0\.0\.1:\\d+",
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.register_blueprint(policy_bp)

# Global error handler for JSON errors
@app.errorhandler(400)
def handle_bad_request(e):
    return {"error": "Bad request: " + str(e)}, 400

@app.errorhandler(500)
def handle_server_error(e):
    return {"error": "Internal server error: " + str(e)}, 500

if __name__ == "__main__":
    print("Starting PolicyAgentX Backend on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)