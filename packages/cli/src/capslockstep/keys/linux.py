import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

from capslockstep.keys.base import CapsLock
import libevdev


class CapsLockLinux(CapsLock):
    def __init__(self) -> None:
        self.dev = libevdev.Device()
        self.dev.name = "Caps Lock Step Device"
        self.dev.enable(libevdev.KEY_CAPSLOCK)
        self.uinput = self.dev.create_uinput_device()
        self.old_value = self.get_current_value()

    async def watch(self) -> AsyncGenerator[bool]:
        while True:
            new_value = self.get_current_value()

            if new_value != self.old_value:
                yield new_value
                self.old_value = new_value

            await asyncio.sleep(0.1)

    def set(self, value: bool) -> None:
        if value != self.get_current_value():
            self.toggle()

    def toggle(self) -> None:
        self.uinput.send_events(
            [
                libevdev.InputEvent(libevdev.KEY_CAPSLOCK, 1),
                libevdev.InputEvent(libevdev.SYN_REPORT, 0),
                libevdev.InputEvent(libevdev.KEY_CAPSLOCK, 0),
                libevdev.InputEvent(libevdev.SYN_REPORT, 0),
            ]
        )

    def get_current_value(self) -> bool:
        return any(
            path.read_text().strip() == "1"
            for path in Path("/sys/class/leds").glob("input*::capslock/brightness")
        )
