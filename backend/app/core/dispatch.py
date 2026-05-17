"""
面孔切换状态机。

DS-001 深筑（技术经理）负责。

六状态定义：
  IDLE / IGNITER / DEEP_MIRROR / EXECUTOR / SPOTLIGHT_TUTOR / SPOTLIGHT_ASK

状态转移链（MVP）：
  IDLE → IGNITER（首次连接，UNKNOWN_RAW）
  IGNITER → DEEP_MIRROR（引信线头被接住，UNKNOWN_ASSESSED）
  DEEP_MIRROR → EXECUTOR / SPOTLIGHT_TUTOR（四步试探法完成，用户类型已识别）
  任意非IDLE → IGNITER（"喘口气" / "随便聊聊"）

注意：
  - 前置判定三问由 FE/BE 协作完成（/api/v1/onboarding/assess），不在此状态机内。
  - dispatch() 依据用户当前 state 决定 persona，不负责执行判定。
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional


class Persona(StrEnum):
    IGNITER = "igniter"
    DEEP_MIRROR = "deep_mirror"
    EXECUTOR = "executor"
    SPOTLIGHT_TUTOR = "spotlight_tutor"
    SPOTLIGHT_ASK = "spotlight_ask"


class UserState(StrEnum):
    UNKNOWN_RAW = "UNKNOWN_RAW"
    UNKNOWN_ASSESSED = "UNKNOWN_ASSESSED"
    BUILDER = "BUILDER"
    USER = "USER"
    HYBRID = "HYBRID"


MODEL_MAP = {
    Persona.IGNITER: "deepseek-chat",
    Persona.DEEP_MIRROR: "deepseek-chat",
    Persona.EXECUTOR: "deepseek-chat",
    Persona.SPOTLIGHT_TUTOR: "deepseek-chat",
    Persona.SPOTLIGHT_ASK: "deepseek-chat",
}

TUTOR_UPGRADE_MODEL = "deepseek-chat"

RESET_PATTERNS = ["随便聊聊", "喘口气", "不想聊这个了", "先这样吧", "换一个话题"]

DEEP_QUESTION_PATTERNS = [
    "为什么", "怎么导致的", "背后逻辑", "原理是什么", "深层原因",
    "根本原因", "如何形成", "底层框架", "怎么推导", "逻辑链",
]


@dataclass
class DispatchResult:
    persona: Persona
    model: str = "deepseek-chat"
    next_state: Optional[UserState] = None

    def to_dict(self) -> dict:
        return {
            "persona": self.persona.value,
            "model": self.model,
        }


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(p in text for p in patterns)


def _is_reset(user_input: str) -> bool:
    return _contains_any(user_input, RESET_PATTERNS)


def _is_executor_call(user_input: str) -> bool:
    exec_patterns = [
        "帮我整理", "帮我萃取", "帮我建模", "帮我出摘要", "帮我做翻译",
        "帮我分析", "帮我拉数据", "帮我查", "帮我看看",
        "请整理", "请分析", "请萃取",
    ]
    return _contains_any(user_input, exec_patterns)


def _is_tutor_call(user_input: str) -> bool:
    tutor_patterns = [
        "陪学模式", "陪我学", "教教我", "讲讲", "解释一下",
        "这是什么", "怎么回事", "帮我拆", "逐条解释",
    ]
    return _contains_any(user_input, tutor_patterns)


def _is_deep_question(user_input: str) -> bool:
    return _contains_any(user_input, DEEP_QUESTION_PATTERNS)


def _count_consecutive_deep(conversation_context: list[dict]) -> int:
    count = 0
    for msg in reversed(conversation_context):
        if msg.get("role") == "user":
            if _is_deep_question(msg.get("content", "")):
                count += 1
            else:
                break
        elif msg.get("role") == "assistant" and msg.get("persona") != "spotlight_tutor":
            break
    return count


def _get_last_persona(conversation_context: list[dict]) -> Optional[str]:
    for msg in reversed(conversation_context):
        if msg.get("role") == "assistant":
            return msg.get("persona")
    return None


def _is_igniter_handoff(user_input: str, conversation_context: list[dict]) -> bool:
    if not conversation_context:
        return False
    last_asst_msgs = [
        m for m in conversation_context
        if m.get("role") == "assistant"
    ]
    if not last_asst_msgs:
        return False
    last_persona_msgs = [
        m for m in last_asst_msgs
        if m.get("persona") == "igniter"
    ]
    return len(last_persona_msgs) > 0 and user_input.strip() != ""


def dispatch(
    user_input: str,
    user_state: dict,
    conversation_context: list[dict],
) -> DispatchResult:
    """
    面孔切换调度核心。

    Args:
        user_input: 用户当前输入
        user_state: {"type": "UNKNOWN_RAW", "step": 0, ...}
        conversation_context: [{"role": "user"/"assistant", "content": "...", "persona": "..."}, ...]
    """
    current_state = user_state.get("type", UserState.UNKNOWN_RAW)

    if _is_reset(user_input):
        return DispatchResult(
            persona=Persona.IGNITER,
            next_state=UserState.UNKNOWN_RAW,
        )

    if current_state == UserState.UNKNOWN_RAW:
        if _is_igniter_handoff(user_input, conversation_context):
            return DispatchResult(
                persona=Persona.DEEP_MIRROR,
                next_state=UserState.UNKNOWN_ASSESSED,
            )
        return DispatchResult(persona=Persona.IGNITER)

    if current_state == UserState.UNKNOWN_ASSESSED:
        if _is_executor_call(user_input):
            return DispatchResult(
                persona=Persona.EXECUTOR,
            )
        last_p = _get_last_persona(conversation_context)
        if last_p and last_p in ("executor", "spotlight_tutor", "spotlight_ask"):
            return DispatchResult(persona=Persona(last_p))
        return DispatchResult(persona=Persona.DEEP_MIRROR)

    if current_state == UserState.BUILDER:
        if _is_reset(user_input):
            return DispatchResult(
                persona=Persona.IGNITER,
                next_state=UserState.UNKNOWN_RAW,
            )
        if _is_executor_call(user_input):
            return DispatchResult(persona=Persona.EXECUTOR)
        if _is_tutor_call(user_input):
            return DispatchResult(persona=Persona.SPOTLIGHT_TUTOR)
        if _is_deep_question(user_input):
            deep_count = _count_consecutive_deep(conversation_context) + 1
            if deep_count >= 2:
                return DispatchResult(
                    persona=Persona.SPOTLIGHT_TUTOR,
                    model=TUTOR_UPGRADE_MODEL,
                )
        last_p = _get_last_persona(conversation_context)
        if last_p and last_p in ("executor", "spotlight_tutor", "spotlight_ask"):
            return DispatchResult(persona=Persona(last_p))
        return DispatchResult(persona=Persona.DEEP_MIRROR)

    if current_state == UserState.USER:
        if _is_reset(user_input):
            return DispatchResult(
                persona=Persona.IGNITER,
                next_state=UserState.UNKNOWN_RAW,
            )
        if _is_executor_call(user_input):
            return DispatchResult(persona=Persona.EXECUTOR)
        last_p = _get_last_persona(conversation_context)
        if last_p and last_p in ("executor", "spotlight_tutor", "spotlight_ask"):
            return DispatchResult(persona=Persona(last_p))
        return DispatchResult(persona=Persona.DEEP_MIRROR)

    if current_state == UserState.HYBRID:
        if _is_reset(user_input):
            return DispatchResult(
                persona=Persona.IGNITER,
                next_state=UserState.UNKNOWN_RAW,
            )
        if _is_executor_call(user_input):
            return DispatchResult(persona=Persona.EXECUTOR)
        if _is_tutor_call(user_input):
            return DispatchResult(persona=Persona.SPOTLIGHT_TUTOR)
        last_p = _get_last_persona(conversation_context)
        if last_p and last_p in ("executor", "spotlight_tutor", "spotlight_ask"):
            return DispatchResult(persona=Persona(last_p))
        return DispatchResult(persona=Persona.DEEP_MIRROR)

    return DispatchResult(persona=Persona.DEEP_MIRROR)
