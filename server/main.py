# ==========================================================================
# JARVIS Core Intelligence & API Gateway: Main Application
# ==========================================================================

import time
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.database import init_db
from server.api.auth_routes import router as auth_router
from server.api.chat_routes import router as chat_router
from server.api.task_routes import router as task_router
from server.api.approval_routes import router as approval_router
from server.api.memory_routes import router as memory_router
from server.api.audit_routes import router as audit_router
from server.api.system_routes import router as system_router
from server.api.research_routes import router as research_router
from server.api.news_routes import router as news_router
from server.api.llm_settings_routes import router as llm_settings_router
from server.api.market_routes import router as market_router

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed default data
    await init_db()
    yield

app = FastAPI(
    title="J.A.R.V.I.S. Personal AI Assistant & Operating Core",
    description="High-performance async agent runtime with multi-tier policy gates, safe tool execution, and episodic memory.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local testing and Android WebView
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(task_router)
app.include_router(approval_router)
app.include_router(memory_router)
app.include_router(audit_router)
app.include_router(system_router)
app.include_router(research_router)
app.include_router(news_router)
app.include_router(llm_settings_router)
app.include_router(market_router)

# Real-time System Vitals Telemetry (for HUD status bars)
@app.get("/api/vitals")
async def get_system_vitals():
    return {
        "battery": 98,
        "isCharging": True,
        "computeLoad": "4.1 TFLOPS",
        "neuralLatency": "3.8 ms",
        "memoryUsage": "52.4%",
        "coreTemp": "308 K",
        "arcOutput": "3.8 GJ/s",
        "status": "ONLINE"
    }

# Bidirectional WebSocket stream for token streaming and HUD sync
@app.websocket("/ws/assistant")
async def assistant_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "J.A.R.V.I.S. Neural Stream Active",
            "status": "ONLINE"
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "STREAM_TOKEN",
                "content": f"Acknowledged: {data}"
            })
    except WebSocketDisconnect:
        pass

# Static file hosting (Serves HUD frontend)
src_dir = WORKSPACE_ROOT / "src"
if src_dir.exists():
    app.mount("/src", StaticFiles(directory=str(src_dir)), name="src")

stitch_dir = WORKSPACE_ROOT / "stitch_jarvis_ai_interface"
if stitch_dir.exists():
    app.mount("/stitch", StaticFiles(directory=str(stitch_dir)), name="stitch")

@app.get("/")
async def serve_index():
    index_file = WORKSPACE_ROOT / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "J.A.R.V.I.S. Core Online. index.html not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
