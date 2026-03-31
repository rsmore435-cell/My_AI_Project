import google.generativeai as genai

# PASTE YOUR KEY HERE
genai.configure(api_key="AIzaSyArXt0A49oFcUKKGdx5LACW4NTGx4nZLTg")

print("------ CHECKING MODELS ------")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"AVAILABLE: {m.name}")
    print("-----------------------------")
except Exception as e:
    print(f"ERROR: {e}")