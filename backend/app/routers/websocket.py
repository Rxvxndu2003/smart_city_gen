"""
WebSocket router for real-time 3D generation updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
import json
import asyncio
from typing import Dict
import time

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[int, list] = {}

@router.websocket("/generation/{project_id}")
async def websocket_generation(
    websocket: WebSocket,
    project_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for live 3D generation updates."""
    await websocket.accept()
    
    # Add connection to active connections
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to 3D generation stream",
            "project_id": project_id,
            "timestamp": time.time()
        })
        
        # Simulate live building generation with progressive updates
        stages = [
            {"stage": "initialization", "progress": 0, "message": "🏗️ Initializing 3D generation..."},
            {"stage": "foundation", "progress": 15, "message": "🔨 Creating foundation..."},
            {"stage": "structure", "progress": 30, "message": "🏢 Building structure..."},
            {"stage": "floors", "progress": 50, "message": "📐 Adding floors..."},
            {"stage": "windows", "progress": 65, "message": "🪟 Installing windows..."},
            {"stage": "materials", "progress": 80, "message": "🎨 Applying materials..."},
            {"stage": "lighting", "progress": 90, "message": "💡 Setting up lighting..."},
            {"stage": "finalization", "progress": 95, "message": "✨ Finalizing model..."},
            {"stage": "export", "progress": 98, "message": "💾 Exporting GLB file..."},
            {"stage": "completed", "progress": 100, "message": "✅ 3D model completed!"},
        ]
        
        for i, stage_data in enumerate(stages):
            await asyncio.sleep(2)  # Simulate processing time
            
            # Send progress update
            await websocket.send_json({
                "type": "progress",
                "stage": stage_data["stage"],
                "progress": stage_data["progress"],
                "message": stage_data["message"],
                "current_step": i + 1,
                "total_steps": len(stages),
                "timestamp": time.time()
            })
            
            # Send intermediate 3D data (simplified mesh data)
            if stage_data["stage"] in ["structure", "floors", "windows"]:
                # Simulate sending simplified mesh data for live preview
                mesh_data = {
                    "vertices": [],  # In production, send actual vertex data
                    "faces": [],     # In production, send actual face data
                    "bounds": {
                        "width": 20,
                        "depth": 15,
                        "height": 30 * (stage_data["progress"] / 100)
                    }
                }
                await websocket.send_json({
                    "type": "mesh_update",
                    "stage": stage_data["stage"],
                    "progress": stage_data["progress"],
                    "mesh": mesh_data,
                    "timestamp": time.time()
                })
        
        # Keep connection alive to receive messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
            
    except WebSocketDisconnect:
        # Remove connection
        if project_id in active_connections:
            active_connections[project_id].remove(websocket)
            if not active_connections[project_id]:
                del active_connections[project_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if project_id in active_connections and websocket in active_connections[project_id]:
            active_connections[project_id].remove(websocket)


async def broadcast_to_project(project_id: int, message: dict):
    """Broadcast message to all connections watching a project."""
    if project_id in active_connections:
        dead_connections = []
        for connection in active_connections[project_id]:
            try:
                await connection.send_json(message)
            except:
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            active_connections[project_id].remove(conn)
        
        if not active_connections[project_id]:
            del active_connections[project_id]
