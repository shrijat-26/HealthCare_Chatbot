# profile_manager.py

import os
import json
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

PROFILE_PATH = "user_profiles.json"

# Setup Azure OpenAI LLM
llm = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT_4o_mini"),
)

# Load all user profiles
def load_all_profiles() -> Dict[str, Dict]:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return {}

# Save updated profiles
def save_profiles(data: Dict[str, Dict]):
    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

# Ensure user profile exists
def ensure_user_profile(user_id: str, name: str = "Unknown", age: str = "Unknown") -> Dict:
    profiles = load_all_profiles()
    if user_id not in profiles:
        profiles[user_id] = {
            "name": name,
            "age": age,
            "conditions": []
        }
        save_profiles(profiles)
    return profiles[user_id]

# Extract health-related information using the LLM
def extract_conditions_from_text(text: str) -> List[str]:
    system_prompt = (
        "You are a highly trained medical assistant. From the following patient-written paragraph, extract all possible medical symptoms or health conditions mentioned, whether explicitly stated or implied. This includes physical symptoms, psychological symptoms, behavioral signs, neurological issues, or any detail relevant to medical diagnosis or history."
        "Do not exclude symptoms that are described in layman terms or as everyday experiences if they could be medically relevant. All pterms like sick , pain, sore throat, body aches, fever, cough, cold, headache, etc should be captured. "
        "Return only a Python list of strings, each representing a distinct symptom or health condition. Do not include general emotions or vague feelings unless they clearly indicate a medical concern."
        "Only return the list — no explanations, no summaries.\n\n"
        f"Text: \"{text}\""
    )

    response = llm.invoke(system_prompt)
    try:
        extracted = eval(response.content.strip())
        if isinstance(extracted, list):
            return [item.strip() for item in extracted]
        return []
    except Exception:
        return []

# Update user profile with timestamped conditions
def log_conditions(user_id: str, transcript: str):
    profiles = load_all_profiles()
    if user_id not in profiles:
        return

    extracted = extract_conditions_from_text(transcript)
    for cond in extracted:
        profiles[user_id]["conditions"].append({
            "condition": cond,
            "timestamp": datetime.now().isoformat()
        })

    save_profiles(profiles)
