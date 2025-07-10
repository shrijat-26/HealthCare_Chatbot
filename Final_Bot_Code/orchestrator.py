# orchestrator.py

import os
import json
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI
from langchain_community.chat_message_histories import FileChatMessageHistory
from emotion_detector import detect_emotion
from dotenv import load_dotenv
from profile_manager import ensure_user_profile, log_conditions  # <-- NEW IMPORT

load_dotenv()

# --------- 1. Define Chat State ----------
class ChatState(TypedDict):
    user_input: dict
    emotion: str
    valence: float
    arousal: float
    transcript: str
    bot_response: str

# --------- 2. Azure LLM Setup ------------
llm = AzureChatOpenAI(
    openai_api_type="azure",
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT_4o_mini"),
)

# --------- 3. Persistent Memory Setup ----
MEMORY_DIR = "chat_memory"
PROFILE_PATH = "user_profiles.json"

def get_memory(thread_id: str) -> FileChatMessageHistory:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    filepath = os.path.join(MEMORY_DIR, f"{thread_id}.json")
    return FileChatMessageHistory(filepath)

def load_user_profile(user_id: str) -> Dict[str, Any]:
    if not os.path.exists(PROFILE_PATH):
        return {}
    with open(PROFILE_PATH, "r") as f:
        profiles = json.load(f)
    return profiles.get(user_id, {})

# --------- 4. Node: Detect Emotion -------
def detect_emotion_node(state: ChatState, config: Dict) -> ChatState:
    user_input = state["user_input"]
    thread_id = config.get("configurable", {}).get("thread_id", "default_user")

    result = detect_emotion(user_input)

    # Show transcript if it's audio
    if user_input["type"] == "audio":
        print(f"\n📝 You (Transcript): {result['transcript']}\n")

    # Ensure profile exists and log new symptoms
    ensure_user_profile(thread_id)
    log_conditions(thread_id, result["transcript"])

    return {
        **state,
        "emotion": result["emotion"],
        "valence": result["valence"],
        "arousal": result["arousal"],
        "transcript": result["transcript"]
    }

# --------- 5. Node: Generate Response -----
def generate_response_node(state: ChatState, config: Dict) -> ChatState:
    thread_id = config.get("configurable", {}).get("thread_id", "default_user")
    memory = get_memory(thread_id)
    profile = load_user_profile(thread_id)

    # Get user message and emotion context
    user_msg = HumanMessage(content=state["transcript"])
    emotion = state["emotion"]

    # Create system message with profile
    conditions = profile.get('conditions', [])
    formatted_conditions = ', '.join([c["condition"] for c in conditions]) if conditions else "None"

    profile_str = (
        f"User Profile:\n"
        f"- Name: {profile.get('name', 'Unknown')}\n"
        f"- Age: {profile.get('age', 'Unknown')}\n"
        f"- Known Conditions: {formatted_conditions}\n\n"
    )

    system_msg = HumanMessage(content=(
        profile_str +
        f"You are a highly empathetic healthcare assistant. "
        f"The user's current emotional state is '{emotion}'. "
        "Respond empathetically and supportively while still being helpful."
    ))

    # Combine memory messages + new prompt
    memory.add_message(user_msg)
    history = memory.messages[-10:]
    full_prompt = [system_msg] + history

    # LLM response
    response = llm.invoke(full_prompt)
    memory.add_message(response)

    return {
        **state,
        "bot_response": response.content
    }

# --------- 6. Build LangGraph -------------
def build_chatbot() -> Runnable:
    workflow = StateGraph(ChatState)

    workflow.add_node("detect_emotion", detect_emotion_node)
    workflow.add_node("generate_response", generate_response_node)

    workflow.set_entry_point("detect_emotion")
    workflow.add_edge("detect_emotion", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()

chatbot = build_chatbot()
