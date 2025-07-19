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
from profile_manager import log_conditions  # <-- NEW IMPORT

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

    # Log new symptoms if transcript exists
    if result["transcript"]:
        log_conditions(thread_id, result["transcript"])

    return {
        **state,
        "emotion": result["emotion"],
        "valence": result["valence"],
        "arousal": result["arousal"],
        "transcript": result["transcript"]
    }

# # --------- 5. Node: Generate Response -----
# def detect_emotion_node(state: ChatState, config: Dict) -> ChatState:
#     user_input = state["user_input"]
#     thread_id = config.get("configurable", {}).get("thread_id", "default_user")

#     result = detect_emotion(user_input)

#     # Show transcript if it's audio
#     if user_input["type"] == "audio":
#         print(f"\n📝 You (Transcript): {result['transcript']}\n")

#     # Ensure profile exists and log new symptoms
#     ensure_user_profile(thread_id)
#     log_conditions(thread_id, result["transcript"])

#     return {
#         **state,
#         "emotion": result["emotion"],
#         "valence": result["valence"],
#         "arousal": result["arousal"],
#         "transcript": result["transcript"]
#     }

# --------- 5. Node: Generate Response -----
def generate_response_node(state: ChatState, config: Dict) -> ChatState:
    thread_id = config.get("configurable", {}).get("thread_id", "default_user")
    memory = get_memory(thread_id)
    profile = load_user_profile(thread_id)

    user_msg = HumanMessage(content=state["transcript"])
    emotion = state["emotion"]

    # Format profile context
    conditions = profile.get('conditions', [])
    formatted_conditions = ', '.join([c["condition"] for c in conditions]) if conditions else "None"
    profile_str = (
        f"User Profile:\n"
        f"- Name: {profile.get('name', 'Unknown')}\n"
        f"- Age: {profile.get('age', 'Unknown')}\n"
        f"- Known Conditions: {formatted_conditions}\n\n"
    )

    # Generate emotion-specific system prompt
    def get_emotion_prompt(emotion: str) -> str:
        emotion = emotion.lower()
        if emotion in ["sad", "angry", "anxious", "frustrated", "upset", "negative"]:
            return (
                f"{profile_str}"
                "You are a calm and supportive healthcare assistant. "
                f"The user is currently feeling {emotion}. "
                "Respond with empathy, be brief, comforting, and directly address their concerns."
            )
        elif emotion in ["happy", "excited", "relieved","positive"]:
            return (
                f"{profile_str}"
                "You are a warm and encouraging healthcare assistant. "
                f"The user is currently feeling {emotion}. "
                "Respond positively, include relevant health information, and feel free to elaborate helpfully."
            )
        else:  # neutral or unrecognized emotion
            return (
                f"{profile_str}"
                "You are a helpful healthcare assistant. "
                f"The user is currently feeling {emotion}. "
                "Respond clearly, respectfully, and offer relevant medical guidance or follow-up questions.Be concise in your response & talk to them as a friend."
            )

    system_msg = HumanMessage(content=get_emotion_prompt(emotion))

    # Add to memory and get LLM response
    memory.add_message(user_msg)
    history = memory.messages[-10:]
    full_prompt = [system_msg] + history

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
