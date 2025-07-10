from typing import TypedDict, List, Union
from langgraph.graph import StateGraph, START, END

from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_models import AzureChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


# Define the state
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]


# LLM Wrapper Class using Azure
class AzureLLM:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT_4o_mini"),
        )

    def get_response(self, messages: List[Union[HumanMessage, AIMessage]]) -> AIMessage:
        response = self.llm.invoke(messages)
        return AIMessage(content=response.content)


# Node class for processing
class ProcessNode:
    def __init__(self, llm: AzureLLM):
        self.llm = llm

    def __call__(self, state: AgentState) -> AgentState:
        response = self.llm.get_response(state["messages"])
        print(f"\nAI: {response.content}")
        state["messages"].append(response)
        return state


# Build the graph
def build_graph(llm: AzureLLM):
    graph = StateGraph(AgentState)
    process_node = ProcessNode(llm)

    graph.add_node("process", process_node)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)

    return graph.compile()


# Main runner
def main():
    azure_llm = AzureLLM()
    app = build_graph(azure_llm)

    conversation_history: List[Union[HumanMessage, AIMessage]] = []

    while True:
        user_input = input("Enter prompt: ")
        if user_input.strip().lower() == "exit":
            break

        conversation_history.append(HumanMessage(content=user_input))
        result = app.invoke({"messages": conversation_history})
        conversation_history = result["messages"]

        #print(result["messages"])

    with open("logging.txt", "w") as file:
        file.write("Your Conversation Log:\n\n")
        for message in conversation_history:
            if isinstance(message, HumanMessage):
                file.write(f"You: {message.content}\n")
            elif isinstance(message, AIMessage):
                file.write(f"AI: {message.content}\n\n")
        file.write("End of Conversation")

    print("Conversation saved to logging.txt")


if __name__ == "__main__":
    main()
