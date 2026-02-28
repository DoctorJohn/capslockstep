from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class CapsLock(ABC):
    @abstractmethod
    def watch(self) -> AsyncGenerator[bool]:
        """Watch for changes to the Caps Lock key state"""

    @abstractmethod
    def set(self, value: bool) -> None:
        """Set the state of the Caps Lock key to the given value."""
