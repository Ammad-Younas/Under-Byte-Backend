from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlmodel import Session, select
from database.connection import get_session, engine
from models.schemas import Room, RoomCreate, Message, MessageCreate, RoomUpdate
from services.websocket_manager import ConnectionManager
from typing import List
import shutil
import os
import uuid

router = APIRouter()
manager = ConnectionManager()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_extension}"
    
    if os.environ.get("VERCEL"):
        upload_dir = "/tmp/uploads"
    else:
        upload_dir = "uploads"
        
    file_path = f"{upload_dir}/{file_name}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Return path relative to mount point
    return {"url": f"/uploads/{file_name}", "filename": file.filename, "type": file.content_type}

@router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate, session: Session = Depends(get_session)):
    existing_room = session.get(Room, room.roomCode)
    if existing_room:
        raise HTTPException(status_code=400, detail="Room already exists")
    
    db_room = Room.from_orm(room)
    session.add(db_room)
    session.commit()
    session.refresh(db_room)
    return db_room

@router.delete("/rooms/{room_code}")
async def delete_room(room_code: str, session: Session = Depends(get_session)):
    room = session.get(Room, room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    messages = session.exec(select(Message).where(Message.roomCode == room_code)).all()
    for msg in messages:
        session.delete(msg)

    await manager.broadcast_to_room(
        {"type": "room_deleted", "data": {}}, 
        room_code
    )
        
    session.delete(room)
    session.commit()
    return {"ok": True}

@router.post("/rooms/{room_code}/join")
async def join_room(room_code: str, guest_name: str, session: Session = Depends(get_session)):
    room = session.get(Room, room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room.guestName = guest_name
    room.status = "active"
    session.add(room)
    session.commit()
    session.refresh(room)
    
    await manager.broadcast_to_room(
        {"type": "room_update", "data": room.dict()}, 
        room_code
    )
    
    return {"ok": True}

@router.post("/rooms/{room_code}/messages")
async def send_message(room_code: str, message: MessageCreate, session: Session = Depends(get_session)):
    room = session.get(Room, room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    db_message = Message(**message.dict(), roomCode=room_code)
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    
    await manager.broadcast_to_room(
        {"type": "new_message", "data": db_message.dict()}, 
        room_code
    )
    
    return db_message

@router.get("/rooms/{room_code}/messages", response_model=List[Message])
async def get_messages(room_code: str, session: Session = Depends(get_session)):
    messages = session.exec(select(Message).where(Message.roomCode == room_code).order_by(Message.timestamp)).all()
    return messages

@router.websocket("/ws/{room_code}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, username: str):
    await manager.connect(websocket, room_code)
    
    # Send initial room state so client knows host name etc.
    with Session(engine) as session:
        room = session.get(Room, room_code)
        if room:
            await websocket.send_json({
                "type": "room_update", 
                "data": room.dict()
            })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)
