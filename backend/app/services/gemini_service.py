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
    """Initialize Gemini using GOOGLE_API_KEY only"""
    global _client, _backend

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    if google_genai is None:
        raise ImportError("google.genai is unavailable in this environment")

    _client = google_genai.Client(api_key=api_key)
    _backend = "google_api_key"


def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Union[str, Dict[str, str]]:
    """Generate response from Gemini using GOOGLE_API_KEY only"""
    global _client, _backend

    try:
        print("\n" + "=" * 60)
        print("🚀 GEMINI REQUEST STARTING")
        print("=" * 60)

        if _client is None:
            initialize_vertex_ai()
        print("✅ Gemini client initialized successfully")

        print("📦 Model: gemini-3.5-flash-lite")
        print(f"📤 Sending prompt ({len(prompt)} characters)...")

        if _client is None:
            raise RuntimeError("Gemini client is not initialized")
        if google_genai_types_module is None:
            raise ImportError("google.genai.types is unavailable")
        google_genai_types = importlib.import_module("google.genai.types")
        response = _client.models.generate_content(
            model="gemini-3.5-flash-lite",
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
