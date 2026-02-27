from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.settings import settings


def channel_key(room_id: str) -> str:
    return f"capslockstep:room:{room_id}:channel"


def state_key(room_id: str) -> str:
    return f"capslockstep:room:{room_id}:state"


async def get_redis_client():
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


ChannelKeyDep = Annotated[str, Depends(channel_key)]
StateKeyDep = Annotated[str, Depends(state_key)]
RedisClientDep = Annotated[Redis, Depends(get_redis_client)]
