from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Optional
from agents.main_agent import MainAgent
from agents.stt_node import SpeechToTextAgent
from agents.context_collection_agent import ContextCollectionAgent
from agents.empathy_response_agent import EmpathyResponseAgent

class AgentState(TypedDict):
    transcribed_text: Optional[str]
    patient_context: Optional[str]
    empathy_reply: Optional[str]

# Initialize graph
builder = StateGraph(AgentState)

builder.add_node("MainAgent", MainAgent().run)
builder.add_node("STT", SpeechToTextAgent().run)
builder.add_node("ContextCollector", ContextCollectionAgent().run)
builder.add_node("EmpathyResponder", EmpathyResponseAgent().run)

# Define edges
builder.set_entry_point("MainAgent")
builder.add_edge("MainAgent", "STT")
builder.add_edge("STT", "ContextCollector")
builder.add_edge("ContextCollector", "EmpathyResponder")
builder.add_edge("EmpathyResponder", END)

# Compile and run
app = builder.compile()

if __name__ == "__main__":
    final_state = app.invoke({})
    print("=== Final State ===")
    print(final_state)
