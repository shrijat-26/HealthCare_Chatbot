import os
import numpy as np
import soundfile as sf
import sounddevice as sd
from orchestrator import chatbot

def load_audio_file(file_path):
    try:
        audio, sr = sf.read(file_path)
        if sr != 16000:
            raise ValueError("Sample rate must be 16kHz")
        return audio, sr
    except Exception as e:
        print(f"Error loading audio: {e}")
        return None, None

def record_audio(duration=10, sr=16000):
    print(f"\n🎙️ Recording... Speak now for {duration} seconds.")
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='int16')
    sd.wait()
    print("✅ Recording complete.\n")
    audio = audio.flatten().astype(np.float32) / 32768
    return audio, sr

def main():
    print("🤖 Bot: Hello, how may I assist you today?")

    while True:
        user_input = input("\n You: ")

        if user_input.strip().upper() == "END":
            print("\nExiting chatbot.")
            break

        inputs = {}

        if user_input.lower().startswith("text "):
            text_content = user_input[5:].strip()
            if not text_content:
                print("Invalid input. Text content is empty.")
                continue

            inputs = {
                "user_input": {
                    "type": "text",
                    "content": text_content
                }
            }

        elif user_input.lower().startswith("audio "):
            command = user_input[6:].strip()

            # 🎤 Use microphone
            if command.lower() == "mic":
                audio, sr = record_audio()
                inputs = {
                    "user_input": {
                        "type": "audio",
                        "content": audio,
                        "sr": sr,
                        "filename": "mic_input.wav"
                    }
                }

            # 📁 Load from file
            elif command.endswith(".wav") and os.path.exists(command):
                audio, sr = load_audio_file(command)
                if audio is None:
                    continue

                inputs = {
                    "user_input": {
                        "type": "audio",
                        "content": audio,
                        "sr": sr,
                        "filename": command
                    }
                }

            else:
                print("Invalid input. Provide a valid .wav file or use 'audio mic' for microphone.")
                continue

        else:
            print("Invalid input format. Use 'text <your text>' or 'audio <yourfile.wav>' or 'audio mic'")
            continue

        final_state = chatbot.invoke(inputs)

        if inputs["user_input"].get("type") == "audio":
            print(f"\n📝 You : {final_state.get('transcript', '[No transcript found]')}\n")

        print("\n🤖 Bot:", final_state.get("bot_response", "I'm here to listen.\n"))

if __name__ == "__main__":
    main()
