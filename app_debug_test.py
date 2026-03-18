import os
from google import genai
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

COLLEGE_CONTEXT = "SRM context info"

def get_gemini_response(prompt, history=[]):
    if not client:
        return "The AI assistant is not fully configured yet."
    
    try:
        system_instruction = f"You are the SRM Student Support AI Assistant.\n\n{COLLEGE_CONTEXT}"
        
        contents = []
        for msg in history:
            role = "user" if msg['role'] == 'user' else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg['content'])]))
        
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

        print(f"DEBUG: Sending request with {len(history)} history messages.")
        
        print("AVAILABLE_MODELS_LIST:")
        for m in client.models.list():
            print(f"MODEL: {m.name}")
        return "LISTED"
        return response.text
    except Exception as e:
        print(f"CRITICAL API ERROR: {e}")
        import traceback
        traceback.print_exc()
        return "ERROR"

if __name__ == "__main__":
    print(get_gemini_response("Who are you?", []))
