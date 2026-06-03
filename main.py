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
# Data Model Design & Persistence
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

DB_FILE = "database.json"
sessions: Dict[str, SessionInfo] = {}

def load_db():
    global sessions
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions = {k: SessionInfo(**v) for k, v in data.items()}
        except Exception:
            sessions = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v.dict() for k, v in sessions.items()}, f, indent=2)

# Load data on startup
load_db()

# Ensure static directory exists for serving frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "<h1>Welcome to Local AI Guest Gateway</h1><p>index.html not found. Please complete Step 5.</p>"

# ==========================================
# Core APIs & New Features
# ==========================================

@app.get("/api/models")
async def get_models():
    """Fetch available models from local Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                return [model["name"] for model in data.get("models", [])]
    except Exception:
        pass
    # Fallback if connection fails
    return ["llama3", "phi3", "mistral"]

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
    save_db()
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

@app.get("/api/admin/analytics")
async def get_analytics():
    """Fetch aggregated analytics for dashboard"""
    total_tokens = sum(s.token_used for s in sessions.values())
    total_requests = len(sessions)
    approved = sum(1 for s in sessions.values() if s.status == "approved")
    rejected = sum(1 for s in sessions.values() if s.status == "rejected")
    all_sessions = [s.dict() for s in sessions.values()]
    return {
        "total_tokens": total_tokens,
        "total_requests": total_requests,
        "approved": approved,
        "rejected": rejected,
        "sessions": all_sessions
    }

@app.post("/api/admin/approve/{session_id}")
async def approve_request(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "approved"
    session.expires_at = time.time() + (2 * 60 * 60)
    session.token_limit = 50000
    save_db()
    
    return {
        "message": f"Session {session_id} approved.", 
        "expires_at": session.expires_at, 
        "token_limit": session.token_limit
    }

@app.post("/api/admin/reject/{session_id}")
async def reject_request(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    session.status = "rejected"
    save_db()
    return {"message": f"Session {session_id} rejected."}


# ==========================================
# Proxy & Billing Module
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/chat"

class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: bool = True

@app.post("/api/chat")
async def chat_proxy(request: Request, chat_req: ChatRequest):
    session_id = request.headers.get("X-Session-ID")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    session = sessions[session_id]
    
    if session.status != "approved":
        raise HTTPException(status_code=403, detail="Session is not approved")
    
    if session.expires_at and time.time() > session.expires_at:
        session.status = "expired"
        save_db()
        raise HTTPException(status_code=403, detail="Session expired")
        
    if session.token_used >= session.token_limit:
        raise HTTPException(status_code=403, detail="Token limit exceeded")

    chat_req.stream = True
    payload = chat_req.dict()

    async def generate() -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", OLLAMA_URL, json=payload, timeout=None) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
                        # Count roughly 1 token per JSON chunk
                        session.token_used += 1
                    save_db()
                        
            except httpx.RequestError as e:
                error_msg = json.dumps({"error": f"Ollama connection error: {str(e)}"})
                yield f"{error_msg}\n".encode("utf-8")

    return StreamingResponse(generate(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
