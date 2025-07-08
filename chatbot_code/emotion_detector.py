# emotion_detector.py

import numpy as np
from emotion_test import remove_silence, stt_transcribe, text_probs, EMOTION_LABELS

def detect_emotion(input_data: dict):
    if input_data["type"] == "text":
        text = input_data["content"]
        probs = text_probs(text)
        emotion = EMOTION_LABELS[np.argmax(probs)]
        valence = probs[2] - probs[0]
        return {
            "emotion": emotion,
            "valence": float(valence),
            "arousal": None,
            "transcript": text
        }

    elif input_data["type"] == "audio":
        audio = input_data["content"]
        sr = input_data["sr"]
        filename = input_data.get("filename", "unknown.wav")

        audio = remove_silence(audio, sr)
        transcript = stt_transcribe(audio, sr)
        probs = text_probs(transcript)
        emotion = EMOTION_LABELS[np.argmax(probs)]
        valence = probs[2] - probs[0]
        arousal = float(np.mean(np.abs(audio)))

        return {
            "emotion": emotion,
            "valence": float(valence),
            "arousal": arousal,
            "transcript": transcript
        }

    else:
        raise ValueError("Input type must be 'text' or 'audio'")
