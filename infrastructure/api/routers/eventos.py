import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import jwt

from application.events import event_bus
from application.security.jwt import decode_token

router = APIRouter(prefix="/eventos", tags=["eventos"])


@router.get("/stream")
async def stream(token: str = Query(...)):
    try:
        decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    queue = event_bus.subscribe()
    event_bus.set_loop(asyncio.get_running_loop())

    async def generar():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(message, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(generar(), media_type="text/event-stream")
