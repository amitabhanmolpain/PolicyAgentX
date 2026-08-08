import os
import importlib
from typing import Any, Dict, Union

try:
    from groq import Groq
except ImportError:
    Groq = None

# Global model instance
_client = None

def initialize_groq():
    """Initialize Groq using GROQ_API_KEY"""
    global _client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")

    if Groq is None:
        raise ImportError("groq is unavailable in this environment")

    _client = Groq(api_key=api_key)

def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Union[str, Dict[str, str]]:
    """Generate response from Groq using GROQ_API_KEY"""
    global _client

    try:
        print("\n" + "=" * 60)
        print("🚀 GROQ REQUEST STARTING")
        print("=" * 60)

        if _client is None:
            initialize_groq()
        print("✅ Groq client initialized successfully")

        print("📦 Model: llama-3.1-8b-instant")
        print(f"📤 Sending prompt ({len(prompt)} characters)...")

        if _client is None:
            raise RuntimeError("Groq client is not initialized")
            
        response = _client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        result_text = response.choices[0].message.content or "No response generated"

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
    """Normalize a Groq response into text."""
    if isinstance(response, dict):
        return response.get("error", "")
    return response or ""


def is_error_response(response: Any) -> bool:
    """Check whether the Groq call returned an error payload."""
    return isinstance(response, dict) and bool(response.get("error"))
