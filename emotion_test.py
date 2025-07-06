import io, wave, json, torch, torchaudio, opensmile
from fastapi import FastAPI, UploadFile
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import webrtcvad
import tempfile
import soundfile as sf
import os
from faster_whisper import WhisperModel
# ---------- 0. MODELS & HELPERS ---------------------------
vad = webrtcvad.Vad(3)  # aggressive VAD
whisper = WhisperModel("tiny", device="cpu", compute_type="int8")

smile = opensmile.Smile(
    feature_set=opensmile.FeatureSet.GeMAPSv01b,
    feature_level=opensmile.FeatureLevel.Functionals,
)

tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
text_net = AutoModelForSequenceClassification.from_pretrained(
    "cardiffnlp/twitter-roberta-base-sentiment"
).eval()

EMOTION_LABELS = ["negative", "neutral", "positive"]

# ---------- 1. UTILITIES ---------------------------
def frame_generator(frame_duration_ms, audio, sample_rate):
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)  # 2 bytes per sample
    offset = 0
    while offset + n <= len(audio):
        yield audio[offset:offset + n]
        offset += n

def remove_silence(waveform, sr=16000):
    assert sr == 16000, "webrtcvad requires 16000Hz sample rate"
    int16_audio = (waveform * 32768).astype("int16").tobytes()

    voiced_frames = []
    for frame in frame_generator(30, int16_audio, sr):
        if vad.is_speech(frame, sr):
            voiced_frames.append(frame)

    if not voiced_frames:
        return np.zeros(1, dtype=np.float32)  # return silence instead of crashing

    combined = b''.join(voiced_frames)
    return np.frombuffer(combined, dtype=np.int16).astype(np.float32) / 32768

def stt_transcribe(audio_np, sr):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio_np, sr)
        segments, _ = whisper.transcribe(tmp.name)
        os.unlink(tmp.name)  # clean up
    return " ".join([seg.text for seg in segments])

def text_probs(text):
    inp = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        p = torch.softmax(text_net(**inp).logits, dim=-1)
    return p.numpy().flatten()

# ---------- 2. FASTAPI ENDPOINT ---------------------------
app = FastAPI()

@app.post("/emotion")
async def emotion(file: UploadFile):
    raw = await file.read()
    wav = wave.open(io.BytesIO(raw))
    sr = wav.getframerate()
    audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    audio = remove_silence(audio, sr)

    # Transcription
    transcript = stt_transcribe(audio, sr)
    p_tx = text_probs(transcript)
    text_emotion = EMOTION_LABELS[np.argmax(p_tx)]

    # Rough valence & arousal
    valence = p_tx[2] - p_tx[0]
    arousal = float(np.mean(np.abs(audio)))  # RMS energy

    return {
        "text_emotion": text_emotion,
        "valence": float(valence),
        "arousal": float(arousal),
        "transcript": transcript.strip()
    }
