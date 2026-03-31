import os
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1.types import content

# Global client instance
_client = None
_project_id = None
_location = None


def initialize_vertex_ai():
    """Initialize Vertex AI with credentials from environment"""
    global _client, _project_id, _location
    
    _project_id = os.getenv("GCP_PROJECT_ID")
    _location = os.getenv("GCP_LOCATION", "us-central1")
    
    if not _project_id:
        raise ValueError("GCP_PROJECT_ID environment variable not set")
    
    # Initialize Vertex AI
    aiplatform.init(project=_project_id, location=_location)
    _client = aiplatform.gapic.PredictionServiceClient()


def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """
    Generate response from Vertex AI Generative AI
    
    Args:
        prompt: The prompt to send to Vertex AI
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum tokens in response
    
    Returns:
        Generated text response
    """
    global _client, _project_id, _location
    
    try:
        print("\n" + "="*60)
        print("🚀 VERTEX AI REQUEST STARTING")
        print("="*60)
        
        if _client is None:
            initialize_vertex_ai()
        print("✅ Vertex AI initialized successfully")
        
        print(f"📦 Model: gemini-2.0-flash-001")
        print(f"📤 Sending prompt ({len(prompt)} characters)...")
        
        # Use Vertex AI's generative AI service
        from vertexai.generative_models import GenerativeModel
        
        model = GenerativeModel("gemini-2.0-flash-001")
        
        response = model.generate_content(
            contents=prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        result_text = response.text if response.text else "No response generated"
        print(f"✅ Response received ({len(result_text)} characters)")
        print(f"\n📝 RESPONSE PREVIEW:\n{result_text[:200]}{'...' if len(result_text) > 200 else ''}")
        print("="*60 + "\n")
        
        return result_text
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"❌ {error_msg}")
        print("="*60 + "\n")
        return error_msg
