import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Session, Message, SessionSummary
from app.schemas.chat import ChatRequest, SessionOut, SessionCreateOut, MessageOut
from app.core.deepseek import stream_chat
from app.core.dispatch import dispatch, DispatchResult, Persona
from app.core.phase_model import detect_phase, format_phase_context, PHASES
from app.core.memory_folding import fold_conversation, get_folded_context, build_context_messages
from app.config import settings

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

    await fold_conversation(session_id, db, max_messages=10, fold_batch=999)

    return {"status": "archived", "folded": True}


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

    user_state = {"type": session.state}

    user_msg = Message(session_id=session_id, role="user", content=body.message)
    db.add(user_msg)
    await db.flush()

    summaries_context, recent_messages = await get_folded_context(
        session_id, db, recent_count=20
    )

    dispatch_result = dispatch(
        user_input=body.message,
        user_state=user_state,
        conversation_context=recent_messages + [{"role": "user", "content": body.message}],
    )
    persona = dispatch_result.persona

    if dispatch_result.next_state:
        session.state = dispatch_result.next_state.value

    messages_for_api = build_context_messages(summaries_context, recent_messages)

    extra_context = ""
    market_keywords = [
        "市场", "行情", "大盘", "仓位", "阶段", "牛市", "熊市", "震荡",
        "恐慌", "抄底", "加仓", "减仓", "清仓", "持仓", "板块", "指数",
        "涨", "跌", "回调", "反弹", "见底", "见顶", "三阶段", "估值",
        "泡沫", "战争", "脱敏", "基本面", "信号不足", "仓位应该",
    ]
    if any(kw in body.message for kw in market_keywords):
        signals = [body.message]
        phase = detect_phase(signals)
        extra_context = format_phase_context(phase)

    async def event_stream():
        full_response = ""
        try:
            async for content_chunk in stream_chat(
                messages=messages_for_api,
                persona=persona.value,
                extra_context=extra_context,
            ):
                full_response += content_chunk
                yield f"data: {json.dumps({'content': content_chunk, 'persona': persona.value})}\n\n"
        except Exception as e:
            error_msg = f"抱歉，我现在无法响应。错误：{str(e)}"
            yield f"data: {json.dumps({'content': error_msg, 'persona': persona.value})}\n\n"

        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=full_response,
            persona=persona.value,
        )
        db.add(assistant_msg)
        await db.flush()

        msg_count_result = await db.execute(
            select(Message).where(Message.session_id == session_id)
        )
        msg_count = len(msg_count_result.scalars().all())
        if msg_count > settings.max_context_messages:
            await fold_conversation(session_id, db)

        yield f"data: {json.dumps({'done': True, 'persona': persona.value})}\n\n"

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


@router.post("/sessions/{session_id}/fold")
async def manual_fold(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    folded = await fold_conversation(session_id, db, max_messages=0, fold_batch=999)

    summaries_result = await db.execute(
        select(SessionSummary)
        .where(SessionSummary.session_id == session_id)
        .order_by(SessionSummary.created_at)
    )
    summaries = summaries_result.scalars().all()

    return {
        "status": "folded" if folded else "no_messages_to_fold",
        "summaries": [
            {"id": str(s.id), "summary_text": s.summary_text[:100], "message_count": s.message_count}
            for s in summaries
        ],
    }
