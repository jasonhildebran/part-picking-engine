import asyncio
import json
import os
import shutil
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Part Picker API")

# Configure CORS
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "200 OK"}

async def mock_sse_generator(prompt: str):
    # Mocking a sequence of LangGraph node executions
    events = [
        {"node": "Triage", "status": "running", "message": f"Analyzing prompt: {prompt}"},
        {"node": "Tier1_API_Search", "status": "running", "message": "Querying Octopart Database..."},
        {"node": "Checker", "status": "running", "message": "Validating constraints and normalizing units..."},
        {"node": "Supervisor", "status": "complete", "message": "Job finished. Part found in cache."}
    ]
    
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(1)

@app.post("/start_job")
async def start_job(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "Analyze component")
    except Exception:
        prompt = "Analyze component"
        
    return StreamingResponse(mock_sse_generator(prompt), media_type="text/event-stream")

@app.post("/ingest_pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
        
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "success", "filename": file.filename, "message": "PDF saved successfully."}
