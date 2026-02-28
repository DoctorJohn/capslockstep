import asyncio
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

    async def receiver():
        while True:
            serialized_state = await websocket.receive_text()
            event = CapsLockEvent.model_validate_json(serialized_state)
            state = CapsLockState(value=event.value, date=datetime.now(UTC))
            serialized_state = state.model_dump_json()

            await redis.set(state_key, serialized_state)
            await redis.publish(channel_key, serialized_state)

    async def sender():
        async for message in pubsub.listen():
            if message["type"] == "message":
                serialized_state = message["data"]
                state = CapsLockState.model_validate_json(serialized_state)
                await websocket.send_text(state.model_dump_json())

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(receiver())
            tg.create_task(sender())

            if serialized_state := await redis.get(state_key):
                state = CapsLockState.model_validate_json(serialized_state)
                await websocket.send_text(state.model_dump_json())
    except* WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel_key)
        await pubsub.aclose()
