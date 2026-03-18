import os
from flask import Flask, request, jsonify
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/test', methods=['POST'])
def test_gemini():
    prompt = request.json.get('prompt', 'Hello')
    print(f"DEBUG: Calling Gemini with prompt: {prompt}")
    try:
        response = client.models.generate_content(
            model='models/gemini-1.5-flash',
            contents=prompt
        )
        print("DEBUG: Response received")
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"DEBUG: Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001)
