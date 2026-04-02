import json
import os
from pathlib import Path
from typing import Any, Dict, Union

import vertexai
from vertexai.preview.generative_models import GenerativeModel

# Global model instance
_model = None
_project_id = None
_location = None


def initialize_vertex_ai():
    """Initialize Vertex AI with service account credentials"""
    global _model, _project_id, _location

    backend_dir = Path(__file__).resolve().parents[2]
    service_account_path = backend_dir / "service-account.json"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(service_account_path)

    _project_id = os.getenv("GCP_PROJECT_ID")
    _location = os.getenv("GCP_LOCATION", "us-central1")

    if not _project_id and service_account_path.exists():
        try:
            with service_account_path.open("r", encoding="utf-8") as handle:
                service_data = json.load(handle)
            _project_id = service_data.get("project_id")
        except Exception:
            _project_id = None

    if not _project_id:
        raise ValueError("GCP_PROJECT_ID environment variable not set")

    vertexai.init(project=_project_id, location=_location)
    _model = GenerativeModel("gemini-2.5-flash")


def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Union[str, Dict[str, str]]:
    """Generate response from Vertex AI Generative AI"""
    global _model

    try:
        print("\n" + "=" * 60)
        print("🚀 VERTEX AI REQUEST STARTING")
        print("=" * 60)

        if _model is None:
            initialize_vertex_ai()
        print("✅ Vertex AI initialized successfully")

        print("📦 Model: gemini-2.5-flash")
        print(f"📤 Sending prompt ({len(prompt)} characters)...")

        response = _model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        result_text = response.text if response.text else "No response generated"
        print(f"✅ Response received ({len(result_text)} characters)")
        print(f"\n📝 RESPONSE PREVIEW:\n{result_text[:200]}{'...' if len(result_text) > 200 else ''}")
        print("=" * 60 + "\n")

        return result_text
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"❌ {error_msg}")
        print("=" * 60 + "\n")
        return {"error": str(e)}


def response_text(response: Union[str, Dict[str, str]]) -> str:
    """Normalize a Gemini response into text."""
    if isinstance(response, dict):
        return response.get("error", "")
    return response or ""


def is_error_response(response: Any) -> bool:
    """Check whether the Gemini call returned an error payload."""
    return isinstance(response, dict) and bool(response.get("error"))
