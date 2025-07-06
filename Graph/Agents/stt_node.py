class SpeechToTextAgent:
    def run(self, state):
        print("Mocking STT for now...")
        # In reality, you'd convert audio input to text here.
        state["transcribed_text"] = "My name is John, I am 42, I have chest pain and diabetes."
        return state
