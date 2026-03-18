import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AIzaSyAR2LssqeAHKUPaZzpSsv1DC82IJX9eJVQ" # Fallback for testing
client = genai.Client(api_key=GEMINI_API_KEY)

try:
    print("AVAILABLE MODELS:")
    models = list(client.models.list())
    for model in models:
        print(f"MODEL_NAME: {model.name}")
    
    if models:
        print(f"\nTesting with first model: {models[0].name}")
        response = client.models.generate_content(
            model=models[0].name,
            contents="Hello"
        )
        print(f"RESPONSE: {response.text}")
except Exception as e:
    print(f"Error listing models: {e}")
