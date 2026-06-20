"""
WebSocket endpoint with Redis pub/sub for real-time alerts.
Clients subscribe on /ws/events?token=<jwt>.
Backend services publish to Redis channel "slashsure:events".
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()

# In-memory registry: user_id → list[WebSocket]
_connections: dict[str, list[WebSocket]] = {}


async def _get_redis():
    """Return a Redis connection from the app-wide pool."""
    from app.core.redis import get_redis
    return await get_redis()


# ── Broadcast helpers (called by background workers) ─────────────────────────

async def broadcast_to_user(user_id: str, payload: dict) -> None:
    for ws in list(_connections.get(user_id, [])):
        try:
            await ws.send_json(payload)
        except Exception:
            _connections[user_id].remove(ws)


async def broadcast_global(payload: dict) -> None:
    for user_id in list(_connections):
        for ws in list(_connections.get(user_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                _connections[user_id].remove(ws)


async def publish_event(event_type: str, data: dict) -> None:
    """Publish to Redis so all backend instances broadcast it."""
    try:
        redis = await _get_redis()
        await redis.publish(
            "slashsure:events",
            json.dumps({"type": event_type, "data": data}),
        )
    except Exception as exc:
        logger.error("Redis publish failed: %s", exc)
        # Fall back to in-process broadcast
        await broadcast_global({"type": event_type, "data": data})


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, token: Optional[str] = None):
    await websocket.accept()

    user_id = "anonymous"
    if token:
        from app.core.security import decode_token
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub", "anonymous")

    _connections.setdefault(user_id, []).append(websocket)
    logger.info("WS connected: %s (total users: %d)", user_id, len(_connections))

    # Start Redis subscriber task for this connection
    sub_task = asyncio.create_task(_redis_subscriber(user_id))

    try:
        await websocket.send_json({"type": "connected", "message": "SlashSure live feed active"})
        while True:
            await asyncio.sleep(25)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("WS error: %s", exc)
    finally:
        sub_task.cancel()
        conns = _connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("WS disconnected: %s", user_id)


async def _redis_subscriber(user_id: str) -> None:
    """Listen to Redis pub/sub and forward messages to this user's WS connections."""
    try:
        redis = await _get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe("slashsure:events")
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                payload = json.loads(message["data"])
                await broadcast_to_user(user_id, payload)
            except Exception:
                pass
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.error("Redis subscriber error: %s", exc)
