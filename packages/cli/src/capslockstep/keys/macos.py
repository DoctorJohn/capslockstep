import asyncio
import ctypes
import ctypes.util
from contextlib import contextmanager
from collections.abc import AsyncGenerator, Generator

from capslockstep.keys.base import CapsLock


class CapsLockMacOS(CapsLock):
    kIOMainPortDefault = 0
    kIOHIDParamConnectType = 1
    kIOHIDCapsLockState = 1

    def __init__(self) -> None:
        if not (iokit_path := ctypes.util.find_library("IOKit")):
            raise RuntimeError("Could not find IOKit library")

        if not (libc_path := ctypes.util.find_library("c")):
            raise RuntimeError("Could not find C library")

        self.iokit = ctypes.cdll.LoadLibrary(iokit_path)
        self.libc = ctypes.cdll.LoadLibrary(libc_path)

        self.iokit.IOServiceMatching.restype = ctypes.c_void_p
        self.iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]

        self.iokit.IOServiceGetMatchingService.restype = ctypes.c_uint32
        self.iokit.IOServiceGetMatchingService.argtypes = [
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]

        self.iokit.IOServiceOpen.restype = ctypes.c_int
        self.iokit.IOServiceOpen.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]

        self.iokit.IOHIDSetModifierLockState.restype = ctypes.c_int
        self.iokit.IOHIDSetModifierLockState.argtypes = [
            ctypes.c_uint32,
            ctypes.c_int,
            ctypes.c_bool,
        ]

        self.iokit.IOHIDGetModifierLockState.restype = ctypes.c_int
        self.iokit.IOHIDGetModifierLockState.argtypes = [
            ctypes.c_uint32,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_bool),
        ]

        self.iokit.IOServiceClose.restype = ctypes.c_int
        self.iokit.IOServiceClose.argtypes = [ctypes.c_uint32]

        self.iokit.IOObjectRelease.restype = ctypes.c_int
        self.iokit.IOObjectRelease.argtypes = [ctypes.c_uint32]

        self.old_value = self.get_current_value()

    async def watch(self) -> AsyncGenerator[bool]:
        while True:
            new_value = self.get_current_value()

            if new_value != self.old_value:
                yield new_value
                self.old_value = new_value

            await asyncio.sleep(0.1)

    def set(self, value: bool = True) -> None:
        with (
            self.get_matching_service("IOHIDSystem") as service,
            self.connect_to_service(service) as connection,
        ):
            self.iokit.IOHIDSetModifierLockState(
                connection.value,
                self.kIOHIDCapsLockState,
                value,
            )

    def get_current_value(self) -> bool:
        with (
            self.get_matching_service("IOHIDSystem") as service,
            self.connect_to_service(service) as connection,
        ):
            state_out = ctypes.c_bool()

            self.iokit.IOHIDGetModifierLockState(
                connection.value,
                self.kIOHIDCapsLockState,
                ctypes.byref(state_out),
            )

            return state_out.value

    @contextmanager
    def get_matching_service(self, service_name: str) -> Generator[ctypes.c_uint32]:
        matching: ctypes.c_void_p = self.iokit.IOServiceMatching(service_name.encode())

        service: ctypes.c_uint32 = self.iokit.IOServiceGetMatchingService(
            self.kIOMainPortDefault,
            matching,
        )

        if not service:
            raise RuntimeError("Could not find service")

        try:
            yield service
        finally:
            self.iokit.IOObjectRelease(service)

    @contextmanager
    def connect_to_service(
        self, service: ctypes.c_uint32
    ) -> Generator[ctypes.c_uint32]:
        task = ctypes.c_uint32.in_dll(self.libc, "mach_task_self_")
        connection = ctypes.c_uint32()

        result: ctypes.c_int = self.iokit.IOServiceOpen(
            service,
            task.value,
            self.kIOHIDParamConnectType,
            ctypes.byref(connection),
        )

        if result != 0:
            raise RuntimeError(f"IOServiceOpen failed with code {result}")

        try:
            yield connection
        finally:
            self.iokit.IOServiceClose(connection.value)
