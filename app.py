import os
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()
gemini_api_key = os.getenv('GOOGLE_API_KEY')


if gemini_api_key:
    print(f"Gemini key exists")
else:
    print(f"Gemini key does not exist")

system_message = "You are an assistant and give a cost estimation for the broken windshield of a car."
user_prompt = "what is the estimated cost for the broken windshield of a car?"
prompts = [
    {"role": "system", "content": system_message},
    {"role": "user", "content": user_prompt}
  ]
genai.configure()
gemini = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=system_message
)

response = gemini.generate_content(user_prompt)
print("Gemini",response.text)
