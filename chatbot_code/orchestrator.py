from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from emotion_detector import detect_emotion
from openai import AzureOpenAI
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv

load_dotenv()


# ----- 1. Define ChatbotState schema -----
class ChatbotState(TypedDict, total=False):
    user_input: dict
    emotion: str
    valence: float
    arousal: Optional[float]
    transcript: str
    bot_response: str

# ----- 2. Azure OpenAI setup -----
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT_4o_mini")

# ----- 3. LangGraph nodes -----
def detect_emotion_node(state):
    user_input = state["user_input"]
    if user_input["type"] == "audio":
        result = detect_emotion(user_input)
    elif user_input["type"] == "text":
        result = detect_emotion(user_input)
    else:
        raise ValueError("Invalid input type")
    return {**state, **result}


def respond_node(state: ChatbotState) -> ChatbotState:
    emotion = state["emotion"]
    transcript = state["transcript"]

    system_prompt = "You are a compassionate and supportive healthcare chatbot. If the user sounds sad, be especially empathetic."
    if emotion == "negative":
        system_prompt += " The user sounds sad or upset, so respond with extra empathy."

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        temperature = 0.7,
        max_tokens = 200
    )

    reply = response.choices[0].message.content
    return {**state, "bot_response": reply}

# ----- 4. Build LangGraph -----
def build_chatbot():
    workflow = StateGraph(ChatbotState)  # Pass schema here

    workflow.add_node("detect_emotion", detect_emotion_node)
    workflow.add_node("respond", respond_node)

    workflow.set_entry_point("detect_emotion")
    workflow.add_edge("detect_emotion", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()

chatbot = build_chatbot()
