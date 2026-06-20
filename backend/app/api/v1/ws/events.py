"""
WebSocket endpoint for live monitoring feed and real-time alerts.
Clients subscribe and receive server-sent events from Redis Streams.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()

# In-memory connection registry: org_id → list of websockets
_connections: dict[str, list[WebSocket]] = {}


async def broadcast_to_org(org_id: str, payload: dict) -> None:
    connections = _connections.get(org_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


async def broadcast_global(payload: dict) -> None:
    """Broadcast to all connected clients (system-level alerts)."""
    for org_id, connections in _connections.items():
        dead = []
        for ws in connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.remove(ws)


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, token: Optional[str] = None):
    await websocket.accept()

    org_id = "global"
    if token:
        from app.core.security import decode_token
        payload = decode_token(token)
        if payload:
            org_id = payload.get("sub", "global")

    if org_id not in _connections:
        _connections[org_id] = []
    _connections[org_id].append(websocket)
    logger.info(f"WebSocket connected: {org_id}, total: {len(_connections[org_id])}")

    try:
        await websocket.send_json({"type": "connected", "message": "SlashSure live feed active"})
        while True:
            # Keep connection alive with ping
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        _connections[org_id].remove(websocket)
        logger.info(f"WebSocket disconnected: {org_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in _connections.get(org_id, []):
            _connections[org_id].remove(websocket)
