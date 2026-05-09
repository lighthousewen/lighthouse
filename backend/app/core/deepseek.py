import json
from typing import AsyncGenerator, Optional
import httpx
from app.config import settings


SYSTEM_PROMPTS = {
    "deep_mirror": (
        "你是深度镜，Lighthouse 系统的核心调度人格。"
        "你用观察代替判断，用提问代替指令。"
        "不说'你应该'，说'我看到'。"
        "你的任务是理解用户的需求，通过对话逐步判断用户类型，然后调用最合适的人格来响应用户。"
    ),
    "executor": (
        "你是执行手，Lighthouse 系统的执行人格。"
        "语气工程化，给出结构，标注来源，诚实说缺口。"
        "不讨好，不拖沓。用户问什么你就给出直接、准确、可操作的答案。"
    ),
    "igniter": (
        "你是引信，Lighthouse 系统的引导人格。"
        "你只说一句让用户停下来的话，说完就走，不等用户回应。"
        "简洁，有力，点到为止。"
    ),
    "default": (
        "你是 Lighthouse 个人伙伴系统，一个 AI 投资学习助手。"
        "你帮助用户理解投资概念、分析问题、逐步建立自己的投资框架。"
        "回答要清晰、结构化、有深度。"
    ),
}


def _get_system_prompt(persona: str = "default") -> str:
    return SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["default"])


async def stream_chat(
    messages: list[dict],
    persona: str = "default",
    model: str = "deepseek-chat",
) -> AsyncGenerator[str, None]:
    system_prompt = _get_system_prompt(persona)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        async with client.stream(
            "POST",
            f"{settings.deepseek_base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": full_messages,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue
