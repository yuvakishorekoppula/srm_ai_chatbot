import requests
import json

# First, log in or have a session
# For testing, we can bypass session if we modify app.py or just use a dummy session.
# But let's try to simulate a real user flow.

session = requests.Session()

# Register (if needed)
print("Registering...")
resp = session.post('http://127.0.0.1:5000/register', data={
    'username': 'Test User',
    'email': 'test@srm.edu',
    'password': 'password123'
})
print(f"Register status: {resp.status_code}")

# Login
print("Logging in...")
resp = session.post('http://127.0.0.1:5000/login', data={
    'email': 'test@srm.edu',
    'password': 'password123'
})
print(f"Login status: {resp.status_code}")

# Send Chat (Non-FAQ)
print("Sending chat (non-FAQ)...")
resp = session.post('http://127.0.0.1:5000/chat', json={
    'message': 'Who is the vice chancellor of SRM IST?'
})

print(f"Chat Response Payload: {resp.text}")
try:
    data = resp.json()
    print(f"AI Response: {data.get('response')}")
except:
    print("Failed to parse JSON")
