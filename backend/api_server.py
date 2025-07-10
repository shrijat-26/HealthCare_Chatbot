from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import soundfile as sf
import io
from orchestrator import chatbot
from main import load_user_profile, save_user_profile
from pydub import AudioSegment

app = FastAPI()

# Allow local dev frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to ["http://localhost:3000"] if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_user_profile(user_id):
    profile = load_user_profile(user_id)
    if not profile:
        # Create a new profile with default values
        save_user_profile(user_id, user_id, "unknown")

@app.post("/text")
async def handle_text(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    user_id = data.get("user_id", "default_user")
    if not messages:
        return JSONResponse(content={"answer": "No message received"}, status_code=400)
    ensure_user_profile(user_id)
    last_message = messages[-1].get("content", "")
    inputs = {
        "user_input": {
            "type": "text",
            "content": last_message
        }
    }
    final_state = chatbot.invoke(inputs, config={"configurable": {"thread_id": user_id}})
    bot_response = final_state.get("bot_response", "I'm here to listen.")
    return {"answer": bot_response}

@app.post("/voice")
async def handle_audio(file: UploadFile = File(...), user_id: str = Form("default_user")):
    ensure_user_profile(user_id)
    contents = await file.read()
    audio_bytes = io.BytesIO(contents)
    filename = file.filename.lower()
    # Convert webm to wav if needed
    if filename.endswith(".webm"):
        audio_segment = AudioSegment.from_file(audio_bytes, format="webm")
        # Resample to 16000 Hz
        audio_segment = audio_segment.set_frame_rate(16000)
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        audio, sr = sf.read(wav_io)
    else:
        audio, sr = sf.read(audio_bytes)
    inputs = {
        "user_input": {
            "type": "audio",
            "content": audio,
            "sr": sr,
            "filename": file.filename
        }
    }
    final_state = chatbot.invoke(inputs, config={"configurable": {"thread_id": user_id}})
    bot_response = final_state.get("bot_response", "I'm here to listen.")
    transcript = final_state.get("transcript", "[No transcript]")
    return {"answer": bot_response, "transcript": transcript} 