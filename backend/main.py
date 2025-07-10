import os
import json
import numpy as np
import soundfile as sf
import sounddevice as sd
from orchestrator import chatbot

PROFILE_PATH = "user_profiles.json"

def load_audio_from_mic(duration=5, sr=16000):
    print("🎙️ Listening... (Speak now)")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    print("✅ Done recording.")
    return audio.flatten(), sr

def load_user_profile(user_id):
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f).get(user_id, None)
    return None

def save_user_profile(user_id, name, age):
    data = {}
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            data = json.load(f)

    data[user_id] = {
        "name": name,
        "age": age,
        "conditions": []  # This will be inferred from chat history over time
    }

    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f, indent=2)
def main():
    user_id = input("Enter your user ID: ").strip()

    # 💾 Check/Create Profile
    profile = load_user_profile(user_id)
    if not profile:
        print("👋 Welcome! Let's set up your profile.")
        name = input("Enter your name: ").strip()
        age = input("Enter your age: ").strip()
        save_user_profile(user_id, name, age)
        print(f"✅ Profile saved for {name}.\n")

    print("🤖 Bot: Hello, how may I assist you today?")

    while True:
        user_input = input("\nYou (type 'text <message>' or 'mic' to record or 'END'): ").strip()

        if user_input.upper() == "END":
            print("👋 Exiting chatbot. Goodbye!")
            break

        inputs = {}

        if user_input.lower().startswith("text "):
            text_content = user_input[5:].strip()
            if not text_content:
                print("⚠️ Please provide some text.")
                continue
            inputs = {
                "user_input": {
                    "type": "text",
                    "content": text_content
                }
            }

        elif user_input.lower() == "mic":
            audio, sr = load_audio_from_mic()
            inputs = {
                "user_input": {
                    "type": "audio",
                    "content": audio,
                    "sr": sr,
                    "filename": "mic_input"  # just a placeholder
                }
            }

        else:
            print("⚠️ Invalid input. Use 'text <msg>' or 'mic'")
            continue

        final_state = chatbot.invoke(inputs, config={"configurable": {"thread_id": user_id}})

        if inputs["user_input"]["type"] == "audio":
            print(f"\n📝 You (Transcript): {final_state.get('transcript', '[No transcript]')}\n")

        print("🤖 Bot:", final_state.get("bot_response", "I'm here to listen."))

if __name__ == "__main__":
    main()

