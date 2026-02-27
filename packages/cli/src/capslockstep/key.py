from abc import ABC, abstractmethod
from pathlib import Path

import libevdev


class CapsLock(ABC):
    @abstractmethod
    def toggle(self) -> None:
        """Toggle the state of the Caps Lock key."""

    @property
    @abstractmethod
    def state(self) -> bool:
        """Return the current state of the Caps Lock key."""


class CapsLockLinux(CapsLock):
    def __init__(self) -> None:
        self.dev = libevdev.Device()
        self.dev.name = "Caps Lock Step Device"
        self.dev.enable(libevdev.KEY_CAPSLOCK)
        self.uinput = self.dev.create_uinput_device()

    def toggle(self) -> None:
        self.uinput.send_events(
            [
                libevdev.InputEvent(libevdev.KEY_CAPSLOCK, 1),
                libevdev.InputEvent(libevdev.SYN_REPORT, 0),
                libevdev.InputEvent(libevdev.KEY_CAPSLOCK, 0),
                libevdev.InputEvent(libevdev.SYN_REPORT, 0),
            ]
        )

    @property
    def state(self) -> bool:
        return any(
            path.read_text().strip() == "1"
            for path in Path("/sys/class/leds").glob("input*::capslock/brightness")
        )
