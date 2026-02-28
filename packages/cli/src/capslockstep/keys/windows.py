import asyncio
import ctypes
from collections.abc import AsyncGenerator

from capslockstep.keys.base import CapsLock


class CapsLockWindows(CapsLock):
    VK_CAPITAL = 0x14
    SCAN_CAPS = 0x3A
    KEYEVENTF_KEYUP = 0x0002

    def __init__(self) -> None:
        self.user32 = ctypes.WinDLL("user32")

        self.user32.GetKeyState.restype = ctypes.c_short
        self.user32.GetKeyState.argtypes = [ctypes.c_int]

        self.user32.keybd_event.restype = None
        self.user32.keybd_event.argtypes = [
            ctypes.c_byte,
            ctypes.c_byte,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
        ]

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
        self.user32.keybd_event(
            self.VK_CAPITAL,
            self.SCAN_CAPS,
            0,
            None,
        )
        self.user32.keybd_event(
            self.VK_CAPITAL,
            self.SCAN_CAPS,
            self.KEYEVENTF_KEYUP,
            None,
        )

    def get_current_value(self) -> bool:
        return bool(self.user32.GetKeyState(self.VK_CAPITAL) & 1)
