#!/usr/bin/env python3
"""
Test script to verify Gemini and Groq APIs are working
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("🧪 API CONFIGURATION TEST")
print("="*60)

# Test 1: Check if API keys are loaded
gemini_key = os.environ.get("GEMINI_API_KEY")
groq_key = os.environ.get("GROQ_API_KEY")

print("\n1️⃣ API KEYS LOADED:")
print(f"   Gemini: {'✅ YES' if gemini_key else '❌ NO'}")
if gemini_key:
    print(f"   Key: {gemini_key[:20]}...{gemini_key[-10:]}")

print(f"   Groq: {'✅ YES' if groq_key else '❌ NO'}")
if groq_key:
    print(f"   Key: {groq_key[:20]}...{groq_key[-10:]}")

# Test 2: Test Gemini API
print("\n2️⃣ TESTING GEMINI API:")
if gemini_key:
    try:
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Analyze this message for toxicity: 'fuck you idiot'. Respond with JSON: {\"toxic\": true/false, \"labels\": [...]}"
                }]
            }],
            "generationConfig": {"temperature": 0}
        }
        
        print("   Sending request to Gemini...")
        response = requests.post(
            f"{endpoint}?key={gemini_key}",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Gemini API is WORKING!")
            data = response.json()
            print(f"   Response: {str(data)[:200]}...")
        else:
            print(f"   ❌ Gemini API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Gemini API Error: {e}")
else:
    print("   ⚠️  Gemini API key not found in .env")

# Test 3: Test Groq API
print("\n3️⃣ TESTING GROQ API:")
if groq_key:
    try:
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in one word"}
            ],
            "temperature": 0.7,
            "max_tokens": 10
        }
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        
        print("   Sending request to Groq...")
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("   ✅ Groq API is WORKING!")
            data = response.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"   Response: {message}")
        else:
            print(f"   ❌ Groq API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Groq API Error: {e}")
else:
    print("   ⚠️  Groq API key not found in .env")

# Test 4: Check other settings
print("\n4️⃣ OTHER SETTINGS:")
print(f"   Threshold: {os.environ.get('TOXICITY_THRESHOLD', '0.5')}")
print(f"   MongoDB URI: {'✅ Set' if os.environ.get('MONGODB_URI') else '❌ Not set'}")
print(f"   USE_GEMINI: {os.environ.get('USE_GEMINI', 'true')}")
print(f"   USE_GROQ_BOT: {os.environ.get('USE_GROQ_BOT', 'true')}")

print("\n" + "="*60)
print("✅ TEST COMPLETE")
print("="*60)
print("\nIf both APIs show ✅ WORKING, they will be used in the app!")
print("If they show ❌ ERROR, check your API keys in .env file")
print("="*60)
