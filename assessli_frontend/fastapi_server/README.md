# FastAPI Server for Assessli Frontend

## Setup

1. (Recommended) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

## Running the Server

Start the FastAPI server with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- The `/text` endpoint accepts POST requests with JSON `{ "messages": [...] }` and responds with `{ "answer": "hi" }`.
- The `/voice` endpoint accepts POST requests with a file (form-data, key: `file`) and responds with `{ "answer": "hi" }`.

## CORS
CORS is enabled for all origins for local development. 