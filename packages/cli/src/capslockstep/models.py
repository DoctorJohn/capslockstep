from datetime import datetime

from pydantic import BaseModel


class CapsLockEvent(BaseModel):
    value: bool


class CapsLockState(BaseModel):
    value: bool
    date: datetime
