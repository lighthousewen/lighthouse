from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Log

router = APIRouter(prefix="/api/v1")


@router.post("/log/system")
async def log_system(body: dict, db: AsyncSession = Depends(get_db)):
    log_entry = Log(
        log_type="system",
        content=body,
    )
    db.add(log_entry)
    return {"status": "logged"}


@router.post("/log/user")
async def log_user(body: dict, db: AsyncSession = Depends(get_db)):
    log_entry = Log(
        log_type="user_feedback",
        feedback_type=body.get("feedback_type"),
        session_id=body.get("session_id"),
        content=body,
        context_snapshot=body.get("context_snapshot"),
    )
    db.add(log_entry)
    return {"status": "logged"}
