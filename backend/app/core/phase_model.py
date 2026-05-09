"""
三阶段九子螺旋循环模型 · 硬编码规则表。

DS-001 深筑（技术经理）负责。
来源：文文「三阶段九子螺旋循环模型」说明文档（2026-04-23）
MVP 为简化版：三大阶段 + unknown 分支。九子阶段的量化信号在实际使用中逐步校准。

核心约束：
  - 不给买卖建议。AI 解释层只做个性化解释。
  - unknown 阶段为安全默认值。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SubPhase:
    id: str
    name: str
    duration: str
    signal: str
    action: str


@dataclass
class Phase:
    id: int
    name: str
    duration_text: str
    core_logic: str
    position_range: str
    sub_phases: list[SubPhase]


PHASES: list[Phase] = [
    Phase(
        id=1,
        name="恐慌冲击期",
        duration_text="1-3周",
        core_logic="所有资产无差别抛售，现金为王",
        position_range="2-3成（睡眠仓位）",
        sub_phases=[
            SubPhase("1-1", "突发冲击期", "第1-3天",
                     "沪指单日跌≥2% / 创业板跌≥3%；90%以上个股下跌",
                     "无条件一键清仓至2成睡眠仓位，不犹豫"),
            SubPhase("1-2", "恐慌蔓延期", "第4-10天",
                     "指数创新低；成交量放大30%以上",
                     "绝对不抄底；不看盘；不听新闻"),
            SubPhase("1-3", "恐慌见底期", "第11-21天",
                     "指数不再创新低；利空消息不跌",
                     "准备第二阶段加仓清单，不动手"),
        ],
    ),
    Phase(
        id=2,
        name="震荡脱敏期",
        duration_text="4-8周",
        core_logic="情绪逐步修复，指数震荡上行，宽基ETF最优",
        position_range="2成→3→4→5成（逐步建仓）",
        sub_phases=[
            SubPhase("2-1", "试探反弹期", "第1-2周",
                     "沪指站稳5日线；成长股率先反弹",
                     "第一次加仓：2成→3成，仅加宽基ETF"),
            SubPhase("2-2", "震荡整固期", "第3-6周",
                     "指数在5-20日线震荡；成交量稳定",
                     "第二次加仓：3成→4成，加行业ETF"),
            SubPhase("2-3", "加速上涨期", "第7-8周",
                     "沪指站稳30日线；成交量持续放大",
                     "最后一次加仓：4成→5成，封顶"),
        ],
    ),
    Phase(
        id=3,
        name="基本面回归期",
        duration_text="6-12个月",
        core_logic="从β收益转向α收益，个股极端分化",
        position_range="5成→6成→逐步回到2成",
        sub_phases=[
            SubPhase("3-1", "估值修复期", "第1-2个月",
                     "指数突破冲击前高点；成交量创近期新高",
                     "1个月内分批清仓宽基ETF；小仓位布局超跌龙头"),
            SubPhase("3-2", "业绩验证期", "第3-8个月",
                     "指数震荡上行；垃圾股开始回调",
                     "集中持仓3-5只行业龙头；单只不超15%"),
            SubPhase("3-3", "泡沫化期", "第9-12个月",
                     "成交量创历史新高；散户开户数激增；媒体鼓吹牛市",
                     "分批减仓，越涨越卖；最终回到2成睡眠仓位"),
        ],
    ),
]

UNKNOWN_PHASE = Phase(
    id=0,
    name="信号不足期",
    duration_text="—",
    core_logic="当前市场信号不足以判断所处阶段",
    position_range="建议保守仓位2-3成",
    sub_phases=[],
)


def get_phase_by_id(phase_id: int) -> Optional[Phase]:
    for p in PHASES:
        if p.id == phase_id:
            return p
    return None


def detect_phase(user_signals: list[str]) -> Phase:
    """
    根据用户提供的市场信号匹配阶段。返回 UNKNOWN_PHASE 若无法匹配。
    """
    if not user_signals:
        return UNKNOWN_PHASE

    phase1_keywords = ["大跌", "暴跌", "恐慌", "崩盘", "熔断", "战争", "黑天鹅", "跌超", "普跌",
                       "创业板跌", "沪指跌", "指数创新低", "遍地跌", "无差别抛售"]
    phase2_keywords = ["反弹", "企稳", "站稳", "震荡", "整固", "板块分化", "修复",
                       "5日线", "20日线", "开始反弹", "不跌了", "横盘",
                       "利空不跌", "不再创新低"]
    phase3_keywords = ["突破前高", "新高", "牛市", "泡沫", "过热", "散户入场",
                       "赚钱效应", "加速上涨", "主升浪", "密集发行", "全民炒股"]

    combined = " ".join(user_signals).lower()

    p1_hits = sum(1 for kw in phase1_keywords if kw in combined)
    p2_hits = sum(1 for kw in phase2_keywords if kw in combined)
    p3_hits = sum(1 for kw in phase3_keywords if kw in combined)

    if p1_hits > p2_hits and p1_hits > p3_hits:
        return PHASES[0]
    elif p2_hits > p1_hits and p2_hits > p3_hits:
        return PHASES[1]
    elif p3_hits > p1_hits and p3_hits > p2_hits:
        return PHASES[2]
    return UNKNOWN_PHASE


def format_phase_context(phase: Optional[Phase] = None) -> str:
    """将阶段规则格式化为可注入 System Prompt 的上下文。"""
    lines: list[str] = [
        "## 当前市场阶段参考（三阶段九子螺旋循环模型）",
        "",
    ]
    if phase and phase.id != 0:
        lines += [
            f"当前阶段：{phase.name}（{phase.duration_text}）",
            f"核心逻辑：{phase.core_logic}",
            f"参考仓位：{phase.position_range}",
        ]
        if phase.sub_phases:
            lines.append("子阶段详情：")
            for sp in phase.sub_phases:
                lines.append(f"  {sp.id} {sp.name}（{sp.duration}）")
                lines.append(f"    量化信号：{sp.signal}")
                lines.append(f"    操作参考：{sp.action}")
    else:
        lines += [
            "当前阶段：信号不足期",
            "说明：当前市场信号不足以判断所处阶段。建议保守仓位2-3成。",
        ]

    lines += [
        "",
        "约束规则：",
        "- 你绝不替用户做投资决策或给买卖建议。",
        "- 你只提供框架性的阶段参考，帮助用户自己思考当前处于什么阶段。",
        "- 如果用户询问具体操作，你只能解释模型规则，不能给个性化操作建议。",
    ]
    return "\n".join(lines)


def get_phase_summary() -> str:
    """返回三阶段模型的简要说明，用于首次介绍。"""
    lines = ["## 三阶段九子螺旋循环模型简介", ""]
    for p in PHASES:
        lines.append(f"第{p.id}阶段：{p.name}（{p.duration_text}）")
        lines.append(f"  仓位范围：{p.position_range}")
        lines.append(f"  核心逻辑：{p.core_logic}")
        lines.append("")
    lines.append("当前暂无有效市场信号，处于信号不足期。")
    return "\n".join(lines)
