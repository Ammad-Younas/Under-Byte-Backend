from typing import Optional, List
from sqlmodel import Field, SQLModel
from datetime import datetime

class RoomBase(SQLModel):
    roomCode: str = Field(primary_key=True)
    hostName: str
    guestName: Optional[str] = None
    roomTimeout: str
    messageTimer: str
    createdAt: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    status: str = "waiting" # waiting, active, expired

class Room(RoomBase, table=True):
    pass

class RoomCreate(RoomBase):
    pass

class RoomUpdate(SQLModel):
    guestName: Optional[str] = None
    status: Optional[str] = None

class MessageBase(SQLModel):
    senderName: str
    content: Optional[str] = None
    fileUrl: Optional[str] = None
    fileType: Optional[str] = None
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

class Message(MessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roomCode: str = Field(foreign_key="room.roomCode")

class MessageCreate(MessageBase):
    pass
