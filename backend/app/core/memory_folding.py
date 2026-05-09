"""
记忆折叠模块。

核心机制：
  每次对话消息数超过阈值时，将最早的一批消息折叠为"认知增量摘要"，
  存入 session_summaries 表。后续对话中，用摘要 + 最近消息替代全量历史，
  减少上下文长度，保留认知连续性。

设计来源：
  个人伙伴系统世界观设定：系统日志供AI记忆折叠——每次对话结束自动生成
  "本次对话改变了什么认知"的提炼，下次启动时深度镜先读取最近几份增量摘要。
"""

import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.config import settings
from app.models import Message, SessionSummary
from app.core.deepseek import stream_chat


SUMMARY_PROMPT = (
    "你是 Lighthouse 系统的日志官。你的任务是对一段对话历史生成「认知增量摘要」。\n\n"
    "请按以下结构输出（用中文，每项不超过2句话）：\n"
    "1. 核心议题：用户本次主要关注什么问题\n"
    "2. 认知变化：用户的理解发生了什么变化（新增/修正/深化了什么认知）\n"
    "3. 用户画像线索：体现了用户的什么特征（思考习惯/知识水平/偏好）\n"
    "4. 悬而未决：还有哪些未解决的问题或卡点\n\n"
    "约束：\n"
    "- 只提炼认知变化，不要复述对话过程\n"
    "- 不确定的信息标注「存疑」\n"
    "- 如果没有明显认知变化，输出「日常交流，无显著认知增量」\n"
)


FOLD_CONTEXT_PROMPT = (
    "以下是你与用户的对话历史摘要。请阅读这些摘要，了解用户的背景和当前状态。\n"
    "这些摘要是按时间顺序排列的认知增量记录。\n"
)


async def generate_summary(
    messages: list[dict],
) -> str:
    if not messages:
        return "无对话记录"

    summary_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    full_response = ""
    try:
        async for chunk in stream_chat(
            messages=[
                {"role": "user", "content": "请为以下对话生成认知增量摘要：\n\n" + json.dumps(
                    [{"role": m["role"], "content": m["content"][:200]} for m in summary_messages[-10:]]
                , ensure_ascii=False)}
            ],
            model="deepseek-chat",
        ):
            full_response += chunk
    except Exception:
        full_response = "摘要生成失败"

    return full_response.strip() if full_response.strip() else "日常交流，无显著认知增量"


async def fold_conversation(
    session_id,
    db: AsyncSession,
    max_messages: int = 50,
    fold_batch: int = 30,
):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    all_messages = result.scalars().all()

    if len(all_messages) <= max_messages:
        return False

    existing_summaries = await db.execute(
        select(SessionSummary)
        .where(SessionSummary.session_id == session_id)
    )
    already_folded_count = sum(s.message_count for s in existing_summaries.scalars().all())

    fold_targets = [
        m for m in all_messages
    ]

    fold_count = min(fold_batch, len(fold_targets))
    messages_to_fold = fold_targets[:fold_count]

    if not messages_to_fold:
        return False

    message_dicts = [
        {"role": m.role, "content": m.content, "persona": m.persona}
        for m in messages_to_fold
    ]

    summary_text = await generate_summary(message_dicts)

    summary = SessionSummary(
        session_id=session_id,
        summary_text=summary_text,
        message_count=fold_count,
        fold_type="auto",
    )
    db.add(summary)

    for msg in messages_to_fold:
        await db.delete(msg)

    return True


async def get_folded_context(
    session_id,
    db: AsyncSession,
    recent_count: int = 20,
) -> tuple[list[dict], list[dict]]:
    summaries_result = await db.execute(
        select(SessionSummary)
        .where(SessionSummary.session_id == session_id)
        .order_by(SessionSummary.created_at)
    )
    summaries = summaries_result.scalars().all()

    recent_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
        .limit(recent_count)
    )
    recent_messages = recent_result.scalars().all()

    summary_dicts = [
        {"role": "system", "content": f"[记忆折叠摘要 {i+1}] {s.summary_text}"}
        for i, s in enumerate(summaries)
    ]

    recent_dicts = [
        {"role": m.role, "content": m.content, "persona": m.persona}
        for m in recent_messages
    ]

    return summary_dicts, recent_dicts


def build_context_messages(
    summary_dicts: list[dict],
    recent_dicts: list[dict],
) -> list[dict]:
    if summary_dicts:
        context = [
            {"role": "system", "content": FOLD_CONTEXT_PROMPT + "\n\n".join(
                s["content"] for s in summary_dicts
            )}
        ]
        context += recent_dicts
        return context

    return recent_dicts
