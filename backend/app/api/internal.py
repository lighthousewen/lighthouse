from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.dispatch import dispatch, DispatchResult

router = APIRouter(prefix="/api/internal")


class DispatchRequest(BaseModel):
    user_input: str
    user_state: dict
    conversation_context: list[dict] = []


class DispatchResponse(BaseModel):
    persona: str
    system_prompt: str
    model: str


@router.post("/dispatch", response_model=DispatchResponse)
async def internal_dispatch(body: DispatchRequest):
    result = dispatch(
        user_input=body.user_input,
        user_state=body.user_state,
        conversation_context=body.conversation_context,
    )
    return DispatchResponse(
        persona=result.persona.value,
        system_prompt="",
        model=result.model,
    )
