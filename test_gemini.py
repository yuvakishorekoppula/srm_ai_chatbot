import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"API Key: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:]}")

client = genai.Client(api_key=GEMINI_API_KEY)

try:
    print("Sending test request to models/gemini-1.5-flash...")
    response = client.models.generate_content(
        model='gemini-1.5-flash', # SDK often maps this, but let's be sure or try gemini-2.0-flash
        contents="Hello, this is a test from the SRM AI Assistant."
    )
    print("Success!")
    print(f"Response: {response.text}")
except Exception as e:
    print("Failure!")
    print(f"Error Type: {type(e)}")
    print(f"Error Message: {e}")
