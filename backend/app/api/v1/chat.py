import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Session, Message
from app.schemas.chat import ChatRequest, SessionOut, SessionCreateOut, MessageOut
from app.core.deepseek import stream_chat

router = APIRouter(prefix="/api/v1")


@router.post("/sessions", response_model=SessionCreateOut)
async def create_session(db: AsyncSession = Depends(get_db)):
    session = Session()
    db.add(session)
    await db.flush()
    return SessionCreateOut(session_id=session.id, state=session.state)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/sessions/{session_id}/archive")
async def archive_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.archived_at = datetime.now(timezone.utc)
    return {"status": "archived"}


@router.post("/chat")
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    if body.session_id:
        result = await db.execute(select(Session).where(Session.id == body.session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = Session()
        db.add(session)
        await db.flush()

    session_id = session.id

    user_msg = Message(session_id=session_id, role="user", content=body.message)
    db.add(user_msg)
    await db.flush()

    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    history = history_result.scalars().all()

    messages_for_api = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    async def event_stream():
        full_response = ""
        try:
            async for content_chunk in stream_chat(
                messages=messages_for_api,
                persona="deep_mirror" if body.mode == "default" else "executor",
            ):
                full_response += content_chunk
                yield f"data: {json.dumps({'content': content_chunk})}\n\n"
        except Exception as e:
            error_msg = f"抱歉，我现在无法响应。错误：{str(e)}"
            yield f"data: {json.dumps({'content': error_msg})}\n\n"

        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=full_response,
            persona="deep_mirror" if body.mode == "default" else "executor",
        )
        db.add(assistant_msg)
        await db.flush()

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-Id": str(session_id),
        },
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()
