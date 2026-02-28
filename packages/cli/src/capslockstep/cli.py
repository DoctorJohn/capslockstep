import argparse
import asyncio
import platform
from contextlib import suppress

import aiohttp

from capslockstep.keys.base import CapsLock
from capslockstep.models import CapsLockEvent, CapsLockState


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room_id", help="The ID of the room to join")
    parser.add_argument("--api-url", default="capslockstep.fastapicloud.dev")
    args = parser.parse_args()

    match platform.system():
        case "Linux":
            from capslockstep.keys.linux import CapsLockLinux

            caps_lock = CapsLockLinux()
        case "Darwin":
            from capslockstep.keys.macos import CapsLockMacOS

            caps_lock = CapsLockMacOS()
        case _:
            raise NotImplementedError(f"Unsupported system: {platform.system()}")

    with suppress(KeyboardInterrupt):
        asyncio.run(stay_lock_step(caps_lock, args.api_url, args.room_id))


async def stay_lock_step(caps_lock: CapsLock, api_url: str, room_id: str) -> None:
    async with (
        aiohttp.ClientSession() as session,
        session.ws_connect(f"wss://{api_url}/{room_id}") as ws,
        asyncio.TaskGroup() as tg,
    ):

        async def writer():
            async for new_value in caps_lock.watch():
                event = CapsLockEvent(value=new_value)
                await ws.send_str(event.model_dump_json())

        tg.create_task(writer())

        async for message in ws:
            if message.type == aiohttp.WSMsgType.TEXT:
                serialized_state = message.data
                state = CapsLockState.model_validate_json(serialized_state)
                caps_lock.set(state.value)
