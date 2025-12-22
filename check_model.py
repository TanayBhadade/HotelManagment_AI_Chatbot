import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load the API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
    exit()

# 2. Configure Gemini
genai.configure(api_key=api_key)

print("🔍 Checking available models for your API key...\n")

try:
    # 3. Ask Google for the list
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")

    print("\n✅ Done. If the list is empty, your API key might be invalid or blocked.")

except Exception as e:
    print(f"❌ Error connecting to Google: {e}")