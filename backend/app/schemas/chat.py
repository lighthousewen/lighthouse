from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class MessageOut(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    persona: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str
    mode: str = "default"


class SessionOut(BaseModel):
    id: UUID
    user_id: Optional[str] = None
    state: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionCreateOut(BaseModel):
    session_id: UUID
    state: str
