import google.generativeai as genai
import os

def list_available_models(api_key=None):
    """
    List all available Gemini models using the provided API key.
    
    Args:
        api_key (str, optional): Google API key. If None, uses GOOGLE_API_KEY from environment.
    
    Returns:
        list: List of available model names
    """
    if api_key:
        genai.configure(api_key=api_key)
    elif "GOOGLE_API_KEY" in os.environ:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    else:
        raise ValueError("No API key provided and no GOOGLE_API_KEY environment variable set")
    
    try:
        models = genai.list_models()
        available_models = [model.name for model in models if "generateContent" in model.supported_generation_methods]
        
        print("Available models:")
        for model in available_models:
            print(f" - {model}")
        
        return available_models
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        return []
