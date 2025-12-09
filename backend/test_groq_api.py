# backend/test_groq_api.py
"""
Test script to verify Groq API key is working
Run: python test_groq_api.py
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("GROQ API KEY VERIFICATION TEST")
print("=" * 70)

# Load environment
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Check API key
api_key = os.getenv("GROQ_API_KEY")
print(f"\n1. Checking .env file...")
print(f"   Location: {env_path}")
print(f"   Exists: {env_path.exists()}")

if not api_key:
    print(f"\n❌ ERROR: GROQ_API_KEY not found!")
    print(f"\nAdd this to {env_path}:")
    print(f"GROQ_API_KEY=gsk_your_actual_key_here")
    sys.exit(1)

print(f"\n2. API Key Found:")
print(f"   Key: {api_key[:10]}...{api_key[-5:]}")
print(f"   Length: {len(api_key)} characters")

# Test API call
print(f"\n3. Testing Groq API...")
import httpx
import asyncio

async def test_api():
    try:
        client = httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        print(f"   Making test API call...")
        
        response = await client.post(
            "/chat/completions",
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'API test successful' in 3 words or less."
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"   ✅ API call successful!")
            print(f"   Response: {message}")
            print(f"\n✅ GROQ API KEY IS WORKING!")
            return True
        else:
            print(f"   ❌ API returned error {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        await client.aclose()

# Run test
success = asyncio.run(test_api())

print("\n" + "=" * 70)
if success:
    print("VERIFICATION COMPLETE - API KEY IS VALID")
    print("\nYour abstractive mode should now work!")
    print("Restart your server: uvicorn src.main:app --reload")
else:
    print("VERIFICATION FAILED")
    print("\nPossible issues:")
    print("1. Invalid API key - get a new one from https://console.groq.com")
    print("2. No internet connection")
    print("3. Groq service is down")
print("=" * 70)