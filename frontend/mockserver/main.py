#run uvicorn main:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

app = FastAPI()

# Allow local dev frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to ["http://localhost:3000"] if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/text")
async def handle_text(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    if not messages:
        return JSONResponse(content={"answer": "No message received"}, status_code=400)

    last_message = messages[-1].get("content", "")
    return {"answer": last_message}


@app.post("/voice")
async def handle_audio(file: UploadFile = File(...)):
    # Save file as .wav
    file_location = f"./uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"answer": "Audio received"}
