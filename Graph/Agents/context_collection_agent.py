from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
load_dotenv()

class ContextCollectionAgent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

    def run(self, state):
        user_input = state["transcribed_text"]
        print("Extracting patient context using LLM...")
        prompt = (
            "Extract patient context from the following message. Return it as JSON:\n"
            "- Name\n- Age\n- Symptoms\n- Problems\n- Medical History\n- Family History\n\n"
            f"Message: {user_input}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        state["patient_context"] = response.content
        return state
