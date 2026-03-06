import asyncio
import json
import os
import shutil
import time
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from graph import app as langgraph_app
from schemas import ExecutionState, JobMetadata, SearchParameters

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

async def streaming_generator(prompt: str):
    # Initialize basic state
    initial_state = ExecutionState(
        job_metadata=JobMetadata(job_id=str(time.time()), timestamp=str(time.time())),
        search_parameters=SearchParameters(query=prompt),
        constraints=[]
    )
    
    try:
        async for output in langgraph_app.astream(initial_state):
            for node_name, state_update in output.items():
                status_msg = state_update.get("status", f"Processed by {node_name}") if hasattr(state_update, "get") else f"Processed {node_name}"
                
                # Format candidates_evaluated for JSON serialization
                state_dict = {}
                if hasattr(state_update, "get") and "candidates_evaluated" in state_update:
                    state_dict["candidates_evaluated"] = [c.model_dump() for c in state_update["candidates_evaluated"]]
                    
                event = {
                    "node": node_name, 
                    "status": "complete", 
                    "message": status_msg,
                    "state": state_dict
                }
                yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'node': 'Error', 'status': 'failed', 'message': str(e)})}\n\n"

@app.post("/start_job")
async def start_job(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "Analyze component")
    except Exception:
        prompt = "Analyze component"
        
    return StreamingResponse(streaming_generator(prompt), media_type="text/event-stream")

@app.post("/ingest_pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
        
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return StreamingResponse(streaming_generator(temp_file_path), media_type="text/event-stream")
