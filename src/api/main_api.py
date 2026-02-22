from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="Sentinel Hub API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory queues for real-time updates
log_queue = asyncio.Queue()
data_queue = asyncio.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "sentinel_hub.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return "<h1>Sentinel Hub Brain Online</h1><p>Dashboard file missing.</p>"

@app.websocket("/ws/bot")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint for the bot to push logs
@app.post("/api/push/log")
async def push_log(log_data: Dict[str, Any]):
    await manager.broadcast(json.dumps({"type": "LOG", "data": log_data}))
    return {"status": "ok"}

# Endpoint for the bot to push live data (prices, P&L)
@app.post("/api/push/data")
async def push_data(data: Dict[str, Any]):
    await manager.broadcast(json.dumps({"type": "DATA", "data": data}))
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
