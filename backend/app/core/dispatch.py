"""
面孔切换调度模块（Week 2 实现）。

DS-001 深筑负责：
- 六状态定义：IDLE / IGNITER / DEEP_MIRROR / EXECUTOR / SPOTLIGHT_TUTOR / SPOTLIGHT_ASK
- 四步试探法：镜面反射 → 原点提问 → 最小响应 → 校准信号
- UNKNOWN_RAW → 前置判定 → UNKNOWN_ASSESSED 链路
"""

from typing import Dict, List, Any


async def dispatch(user_input: str, user_state: Dict[str, Any], conversation_context: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    POST /api/internal/dispatch 的内部实现。

    当前为骨架，第二周填充状态机逻辑。
    """
    return {
        "persona": "deep_mirror",
        "system_prompt": "",
        "model": "deepseek-chat",
    }
