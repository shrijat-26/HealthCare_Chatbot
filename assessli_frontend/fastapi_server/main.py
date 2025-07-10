from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/text")
async def text_endpoint(request: Request):
    data = await request.json()
    # Optionally, you can inspect data['messages'] here
    return JSONResponse(content={"answer": "hi"})

@app.post("/voice")
async def voice_endpoint(file: UploadFile = File(...)):
    # Optionally, you can process the file here
    return JSONResponse(content={"answer": "hi"}) 