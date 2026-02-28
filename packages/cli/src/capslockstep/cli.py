import argparse
import asyncio
import platform
from contextlib import suppress

import aiohttp

from capslockstep.key import CapsLock, CapsLockLinux


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room_id", help="The ID of the room to join")
    parser.add_argument("--api-url", default="capslockstep.fastapicloud.dev")
    args = parser.parse_args()

    match platform.system():
        case "Linux":
            caps_lock = CapsLockLinux()
        case _:
            raise NotImplementedError(f"Unsupported system: {platform.system()}")

    asyncio.run(stay_lock_step(caps_lock, args.api_url, args.room_id))


async def stay_lock_step(caps_lock: CapsLock, api_url: str, room_id: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"wss://{api_url}/caps-lock/{room_id}") as ws:

            async def writer():
                with suppress(asyncio.CancelledError):
                    async for new_state in caps_lock.watch():
                        event = {"value": new_state}
                        await ws.send_json(event)

            writer_task = asyncio.create_task(writer())

            try:
                async for message in ws:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        state = message.json()
                        value = state["value"]
                        caps_lock.set(value)
            except asyncio.CancelledError:
                pass
            finally:
                writer_task.cancel()
                await writer_task
