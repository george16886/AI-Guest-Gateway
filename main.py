from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, AsyncGenerator
import uuid
import time
import os
import json
import httpx

app = FastAPI(title="Local AI Guest Gateway")

# ==========================================
# Step 1: Data Model Design
# ==========================================

class GuestRequest(BaseModel):
    guest_name: str

class SessionInfo(BaseModel):
    session_id: str
    guest_name: str
    status: str  # "pending", "approved", "rejected"
    token_used: int = 0
    token_limit: int = 0
    expires_at: Optional[float] = None
    created_at: float

# In-memory storage for sessions
# Key: session_id, Value: SessionInfo
sessions: Dict[str, SessionInfo] = {}

# Ensure static directory exists for serving frontend later
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    # Serves the static index.html which will be created in Step 5
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "<h1>Welcome to Local AI Guest Gateway</h1><p>index.html not found. Please complete Step 5.</p>"


# ==========================================
# Step 2: FastAPI Backend Core APIs
# ==========================================

@app.post("/api/request_access")
async def request_access(req: GuestRequest):
    """Guest submits a request for access"""
    session_id = str(uuid.uuid4())
    session_info = SessionInfo(
        session_id=session_id,
        guest_name=req.guest_name,
        status="pending",
        created_at=time.time()
    )
    sessions[session_id] = session_info
    return {"session_id": session_id, "message": "Access request submitted. Waiting for approval."}

@app.get("/api/status/{session_id}", response_model=SessionInfo)
async def get_status(session_id: str):
    """Guest polls for status"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.get("/api/admin/pending", response_model=List[SessionInfo])
async def get_pending_requests():
    """Host dashboard fetches pending requests"""
    return [s for s in sessions.values() if s.status == "pending"]

@app.post("/api/admin/approve/{session_id}")
async def approve_request(session_id: str):
    """Host approves a specific session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "approved"
    # Default: 2 hours expiry
    session.expires_at = time.time() + (2 * 60 * 60)
    # Default: 50,000 tokens limit
    session.token_limit = 50000
    
    return {
        "message": f"Session {session_id} approved.", 
        "expires_at": session.expires_at, 
        "token_limit": session.token_limit
    }

@app.post("/api/admin/reject/{session_id}")
async def reject_request(session_id: str):
    """Host rejects a specific session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "rejected"
    return {"message": f"Session {session_id} rejected."}


# ==========================================
# Step 4: FastAPI Proxy & Billing Module
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/chat"

class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: bool = True

@app.post("/api/chat")
async def chat_proxy(request: Request, chat_req: ChatRequest):
    # Get session_id from headers
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing X-Session-ID header")
    
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    session = sessions[session_id]
    
    if session.status != "approved":
        raise HTTPException(status_code=403, detail="Session is not approved")
    
    if session.expires_at and time.time() > session.expires_at:
        session.status = "expired"
        raise HTTPException(status_code=403, detail="Session expired")
        
    if session.token_used >= session.token_limit:
        raise HTTPException(status_code=403, detail="Token limit exceeded")

    # We enforce streaming for our UI
    chat_req.stream = True
    payload = chat_req.dict()

    async def generate() -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient() as client:
            try:
                # Forward request to Ollama
                async with client.stream("POST", OLLAMA_URL, json=payload, timeout=None) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        # We just forward the chunk
                        yield chunk
                        
                        # A rough token count tracking: 
                        # Increment token_used. Ollama returns json lines. 
                        # We'll just count roughly 1 token per JSON chunk received.
                        # Real implementation might parse the 'eval_count' from the final JSON chunk.
                        session.token_used += 1
                        
            except httpx.RequestError as e:
                # Yield a JSON error message formatted similarly to Ollama
                error_msg = json.dumps({"error": f"Ollama connection error: {str(e)}"})
                yield f"{error_msg}\n".encode("utf-8")

    return StreamingResponse(generate(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    # Run the server with: uvicorn main:app --reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
