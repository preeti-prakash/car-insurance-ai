import os
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv
import base64

# Load API keys from .env
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Validate Gemini key
if not google_api_key:
    raise ValueError("Gemini API key not found in .env")


# Configure Gemini
genai.configure(api_key=google_api_key)

# Gemini Model
model = genai.GenerativeModel("gemini-1.5-flash")

# Prompt template
SYSTEM_PROMPT = """You are an expert car insurance assistant. When a user uploads a damaged car image and describes the accident, analyze the damage and provide a structured estimate like:

---
**Car Insurance Damage Report**
- Detected Parts Damaged: [e.g., Front Bumper, Left Headlight]
- Damage Severity: [Mild / Moderate / Severe]
- Estimated Repair Costs:
  - Front Bumper: $500
  - Left Headlight: $300
- Total Estimated Claim: $800

If the image is unclear, mention that the image is not sufficient.
"""


# Image encoder
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
    

def generate_insurance_response(user_prompt, image):
    # One-shot instruction + user context
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser Description:\n{user_prompt.strip()}"

    parts = [{"text": full_prompt}]
    
    if image:
        encoded_image = encode_image_to_base64(image)
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": encoded_image
            }
        })

    # Streaming Gemini response
    response = model.generate_content(
        contents=[{"role": "user", "parts": parts}],
        stream=True
    )

    result = ""
    for chunk in response:
        if hasattr(chunk, "text"):
            result += chunk.text
            yield result



#gradio UI
            
gr.Interface(
    fn=generate_insurance_response,
    inputs=[
        gr.Textbox(label="Describe the incident and visible damages"),
        gr.Image(label="Upload a damaged car image", type="filepath")
    ],
    outputs=gr.Textbox(label="Insurance Estimate (from Gemini)"),
    title="🚗 Car Insurance Estimator (Gemini AI)",
    description="Upload a photo of the damaged vehicle and describe the incident to get an insurance estimate.",
    allow_flagging="never"
).launch(inbrowser=True)