import os
import google.generativeai as genai


def initialize_gemini():
    """Initialize Gemini with API key from environment"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=api_key)


def generate(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """
    Generate response from Gemini API
    
    Args:
        prompt: The prompt to send to Gemini
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum tokens in response
    
    Returns:
        Generated text response
    """
    try:
        initialize_gemini()
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text if response.text else "No response generated"
    except Exception as e:
        return f"Error generating response: {str(e)}"
