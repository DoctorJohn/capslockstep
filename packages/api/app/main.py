import asyncio
from contextlib import suppress
from datetime import UTC, datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.deps import ChannelKeyDep, RedisClientDep, StateKeyDep
from app.models import CapsLockEvent, CapsLockState

app = FastAPI()


@app.websocket("/{room_id}")
async def caps_lock_ws(
    websocket: WebSocket,
    redis: RedisClientDep,
    channel_key: ChannelKeyDep,
    state_key: StateKeyDep,
):
    await websocket.accept()

    pubsub = redis.pubsub()
    await pubsub.subscribe(channel_key)

    async def reader():
        with suppress(asyncio.CancelledError):
            async for message in pubsub.listen():
                if message["type"] == "message":
                    serialized_state = message["data"]
                    state = CapsLockState.model_validate_json(serialized_state)
                    await websocket.send_text(state.model_dump_json())

    reader_task = asyncio.create_task(reader())

    try:
        if serialized_state := await redis.get(state_key):
            state = CapsLockState.model_validate_json(serialized_state)
            await websocket.send_text(state.model_dump_json())

        while True:
            serialized_state = await websocket.receive_text()
            event = CapsLockEvent.model_validate_json(serialized_state)
            state = CapsLockState(value=event.value, date=datetime.now(UTC))
            serialized_state = state.model_dump_json()

            await redis.set(state_key, serialized_state)
            await redis.publish(channel_key, serialized_state)
    except WebSocketDisconnect:
        pass
    finally:
        reader_task.cancel()
        await reader_task
        await pubsub.unsubscribe(channel_key)
        await pubsub.aclose()
