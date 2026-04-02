import os
import google.generativeai as genai

# Global client instance
_client = None


def initialize_gemini():
    """Initialize Gemini AI with API key from environment"""
    global _client
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    print(f"🔑 Using API key: {api_key[:20]}...")
    
    # Configure Gemini with API key
    genai.configure(api_key=api_key)
    _client = genai.GenerativeModel("gemini-2.5-flash")
    print("✅ Gemini client configured successfully")


def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """
    Generate response from Google Gemini AI
    
    Args:
        prompt: The prompt to send to Gemini
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum tokens in response
    
    Returns:
        Generated text response
    """
    global _client
    
    try:
        print("\n" + "="*60)
        print("🚀 GEMINI AI REQUEST STARTING")
        print("="*60)
        
        if _client is None:
            initialize_gemini()
        print("✅ Gemini AI initialized successfully")
        
        print(f"📦 Model: gemini-2.5-flash")
        print(f"📤 Sending prompt ({len(prompt)} characters)...")
        
        response = _client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
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
