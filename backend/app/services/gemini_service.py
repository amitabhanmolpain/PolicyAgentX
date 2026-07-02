import json
import os
from pathlib import Path
import importlib
from typing import Any, Dict, Union

try:
    from google import genai as google_genai
except ImportError:
    google_genai = None

try:
    from google import genai as google_genai_types_module
except ImportError:
    google_genai_types_module = None

# Global model instance
_model = None
_project_id = None
_location = None
_client = None
_backend = None


def initialize_vertex_ai():
    """Initialize Vertex AI with service account credentials"""
    global _model, _client, _project_id, _location, _backend

    backend_dir = Path(__file__).resolve().parents[2]
    service_account_path = backend_dir / "service-account.json"
    api_key = os.getenv("GOOGLE_API_KEY")

    if api_key:
        if google_genai is None:
            raise ImportError("google.genai is unavailable in this environment")
        _client = google_genai.Client(api_key=api_key)
        _backend = "google_api_key"
        return

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

    try:
        vertexai_module = importlib.import_module("vertexai")
        generative_models_module = importlib.import_module("vertexai.preview.generative_models")
        GenerativeModel = getattr(generative_models_module, "GenerativeModel")
        vertexai_module.init(project=_project_id, location=_location)
        _model = GenerativeModel("gemini-2.5-flash")
        _backend = "vertexai"
        return
    except ImportError:
        pass

    if google_genai is None:
        raise ImportError("Neither vertexai nor google.genai is available in this environment")

    _client = google_genai.Client(vertexai=True, project=_project_id, location=_location)
    _backend = "google_genai"


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

        if _backend == "vertexai" and _model is not None:
            response = _model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            result_text = response.text if response.text else "No response generated"
        else:
            if _client is None:
                raise RuntimeError("Gemini client is not initialized")
            if google_genai_types_module is None:
                raise ImportError("google.genai.types is unavailable")
            google_genai_types = importlib.import_module("google.genai.types")
            response = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=google_genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            result_text = getattr(response, "text", None) or "No response generated"

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
