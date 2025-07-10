import os
import numpy as np
import soundfile as sf
import sounddevice as sd
import webrtcvad
import collections
import sys
from orchestrator import chatbot

vad = webrtcvad.Vad(2)  # Medium aggressiveness

def record_audio_auto_stop(sample_rate=16000, frame_duration_ms=30, padding_duration_ms=300):
    frame_size = int(sample_rate * frame_duration_ms / 1000)
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    print("🎙️ Recording... Speak now. (auto-stops when silence is detected)")

    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []

    def audio_callback(indata, frames, time, status):
        nonlocal triggered, voiced_frames, ring_buffer
        if status:
            print(status, file=sys.stderr)

        for i in range(0, len(indata), frame_size):
            frame = indata[i:i+frame_size]
            if len(frame) < frame_size:
                break
            pcm_data = (frame * 32768).astype(np.int16).tobytes()
            is_speech = vad.is_speech(pcm_data, sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    voiced_frames.extend(f for f, s in ring_buffer)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    raise sd.CallbackStop

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32',
                            blocksize=frame_size, callback=audio_callback):
            sd.sleep(10000)  # Max wait time
    except sd.CallbackStop:
        pass

    if not voiced_frames:
        print("❌ No speech detected.")
        return None, None

    audio = np.concatenate(voiced_frames, axis=0).flatten()
    print("✅ Recording complete.")
    return audio, sample_rate

def main():
    print("🤖 Bot: Hello, how may I assist you today?")

    while True:
        user_input = input("\n You (type 'text <message>' or 'voice', or 'END' to exit): ")

        if user_input.strip().upper() == "END":
            print("\nExiting chatbot.")
            break

        inputs = {}

        if user_input.lower().startswith("text "):
            text_content = user_input[5:].strip()
            if not text_content:
                print("❌ Invalid input. Text content is empty.")
                continue

            inputs = {
                "user_input": {
                    "type": "text",
                    "content": text_content
                }
            }

        elif user_input.lower().strip() == "voice":
            try:
                audio, sr = record_audio_auto_stop()
                if audio is None:
                    continue
            except Exception as e:
                print(f"❌ Failed to record audio: {e}")
                continue

            inputs = {
                "user_input": {
                    "type": "audio",
                    "content": audio,
                    "sr": sr,
                    "filename": "mic_input.wav"
                }
            }

        else:
            print("❌ Invalid input format. Use 'text <your message>' or type 'voice'")
            continue

        final_state = chatbot.invoke(inputs)

        if inputs["user_input"].get("type") == "audio":
            print(f"\n📝 You (transcript): {final_state.get('transcript', '[No transcript found]')}")

        print("\n🤖 Bot:", final_state.get("bot_response", "I'm here to listen."))

if __name__ == "__main__":
    main()
