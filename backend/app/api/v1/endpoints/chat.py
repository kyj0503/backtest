"""
간단한 Redis 기반 채팅 WebSocket
"""
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header, HTTPException
from redis import asyncio as aioredis

from ....core.config import settings
from .auth import require_user
from ....services.yfinance_db import _get_engine
from sqlalchemy import text

router = APIRouter()


async def _get_username(user_id: int) -> str:
    engine = _get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT username FROM users WHERE id=:id"), {"id": user_id}).fetchone()
        return row[0] if row else f"user_{user_id}"


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str, authorization: Optional[str] = Header(None)):
    # FastAPI does not pass headers directly to websocket function; token can be passed as query param `token`
    token = websocket.query_params.get('token')
    user_id: Optional[int] = None
    try:
        # accept first to be able to send close frames
        await websocket.accept()
        # validate token via HTTP helper (bearer <token>)
        if not token and authorization:
            # not expected in WS, but fallback
            token = authorization.split(' ', 1)[1] if authorization and ' ' in authorization else None
        if not token:
            await websocket.close(code=4001)
            return
        # reuse validate logic
        user_id = require_user(f"Bearer {token}")
    except HTTPException:
        await websocket.close(code=4001)
        return

    username = await _get_username(user_id)
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    channel = f"chat:{room}"
    await pubsub.subscribe(channel)

    async def reader():
        async for msg in pubsub.listen():
            if msg is None:
                continue
            if msg.get('type') != 'message':
                continue
            data = msg.get('data')
            await websocket.send_text(data)

    import asyncio
    reader_task = asyncio.create_task(reader())

    # notify join
    await redis.publish(channel, json.dumps({"type": "system", "user": username, "message": f"{username} 님이 입장했습니다."}))
    try:
        while True:
            data = await websocket.receive_text()
            payload = {"type": "chat", "user": username, "message": data}
            await redis.publish(channel, json.dumps(payload))
    except WebSocketDisconnect:
        await redis.publish(channel, json.dumps({"type": "system", "user": username, "message": f"{username} 님이 퇴장했습니다."}))
    finally:
        reader_task.cancel()
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis.close()

