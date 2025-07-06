from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
load_dotenv()

class EmpathyResponseAgent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

    def run(self, state):
        context = state.get("patient_context", "")
        print("Generating empathetic response...")
        prompt = (
            "Given the patient context below, respond empathetically and offer help:\n"
            f"{context}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["empathy_reply"] = response.content
        return state
