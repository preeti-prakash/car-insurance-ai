import os
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv
import base64
from google.cloud import bigquery

# Load API keys and credentials
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("Gemini API key not found in .env")

# Configure Gemini
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Prompt template
SYSTEM_PROMPT = """

Follow these instructions:
You are an expert car insurance assistant helping users estimate repair costs based on two inputs:
1. The user's description of the incident.
2. A photo of the damaged car.

Follow these rules:

Step 1: Analyze the user's description. If specific damaged parts are mentioned, use them to prioritize your damage report.

Step 2: Use the uploaded image to verify the description and check for visible damage. If the image shows no clear damage:
- Politely mention that the car appears undamaged from the image.
- Ask the user to upload a more detailed close-up image of the damage, or describe internal issues if any.

Step 3: If the image contradicts the description (e.g., user says bumper is damaged but image shows it's intact), say: "The image does not show visible signs of the described damage. Please confirm or upload a clearer image."

Step 4: If both the image and description are unclear, respond with: "Insufficient data to estimate the cost."

Step 5: Estimate repair costs using the provided reference table.

Output Format:
---
**Car Insurance Damage Report**
- Detected Parts Damaged: [List] 
- Damage Severity: [Mild / Moderate / Severe]
- Estimated Repair Costs:
  - Part: $Amount
- Total Estimated Claim: $Amount
---

If applicable:
- Note: The car appears undamaged in the image provided. Please upload a more detailed photo or describe internal damage.

"""

# Set up BigQuery client
bq_client = bigquery.Client()

def get_reference_costs():
    query = """
        SELECT Part, Avg_Cost_USD
        FROM `autocloud-gcp.car_insurance_demo.vehicle_table`
        WHERE Part IS NOT NULL AND Avg_Cost_USD IS NOT NULL
        LIMIT 100
    """
    results = bq_client.query(query).result()
    cost_data = "\n".join([f"- {row.Part}: ${row.Avg_Cost_USD}" for row in results])
    return f"\n\n### Reference Repair Costs (from BigQuery):\n{cost_data}"

# Image encoder
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Main Gemini response logic
def generate_insurance_response(user_description, image):
    reference_costs = get_reference_costs()

    # User prompt construction
    user_prompt = f"""User Description:{user_description.strip() if user_description else "No description provided."}
    Image: {'Provided' if image else 'Not provided'}"""
    
    full_prompt = f"""{SYSTEM_PROMPT}{reference_costs}{user_prompt}"""

    parts = [{"text": full_prompt}]
    
    if image:
        encoded_image = encode_image_to_base64(image)
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": encoded_image
            }
        })

    # Gemini streaming
    response = model.generate_content(
        contents=[{"role": "user", "parts": parts}],
        stream=True
    )

    result = ""
    for chunk in response:
        if hasattr(chunk, "text"):
            result += chunk.text
            yield result


# UI
gr.Interface(
    fn=generate_insurance_response,
    inputs=[
        gr.Textbox(label="Describe the incident and visible/internal damages"),
        gr.Image(label="Upload a damaged car image", type="filepath")
    ],
    outputs=gr.Textbox(label="Insurance Estimate (from Gemini)"),
    title=" Car Insurance Estimator",
    description="Describe the accident and upload a car image. Gemini AI uses your input and BigQuery repair cost data to provide a claim estimate.",
    allow_flagging="never"
).launch(inbrowser=True)
# ).launch(server_name="0.0.0.0", server_port=8080)
