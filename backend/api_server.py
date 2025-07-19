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

@app.post("/check-user")
async def check_user(request: Request):
    """Check if user exists and return profile status"""
    data = await request.json()
    user_id = data.get("user_id", "")
    
    if not user_id:
        return JSONResponse(content={"error": "User ID is required"}, status_code=400)
    
    profile = load_user_profile(user_id)
    
    if profile:
        return {
            "exists": True,
            "profile": profile
        }
    else:
        return {
            "exists": False,
            "profile": None
        }

@app.post("/create-profile")
async def create_profile(request: Request):
    """Create a new user profile"""
    data = await request.json()
    user_id = data.get("user_id", "")
    name = data.get("name", "")
    age = data.get("age", "")
    
    if not user_id or not name or not age:
        return JSONResponse(content={"error": "User ID, name, and age are required"}, status_code=400)
    
    # Check if user already exists
    existing_profile = load_user_profile(user_id)
    if existing_profile:
        return JSONResponse(content={"error": "User already exists"}, status_code=409)
    
    # Create new profile
    save_user_profile(user_id, name, age)
    
    return {
        "success": True,
        "message": f"Profile created for {name}",
        "profile": {
            "user_id": user_id,
            "name": name,
            "age": age
        }
    }

@app.post("/text")
async def handle_text(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    user_id = data.get("user_id", "default_user")
    if not messages:
        return JSONResponse(content={"answer": "No message received"}, status_code=400)
    
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