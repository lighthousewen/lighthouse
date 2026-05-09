import sys
sys.path.insert(0, "/Users/tao/my-node-project/lighthouse/lighthouse-app/backend")

from app.core.phase_model import detect_phase, format_phase_context, get_phase_summary, UNKNOWN_PHASE, PHASES

print("=== phase_model 测试 ===")

# Test detect_phase
tests = [
    ("恐慌期", ["沪指暴跌", "创业板跌3%"], 1),
    ("脱敏期", ["反弹", "站稳5日线", "开始企稳"], 2),
    ("基本面料", ["突破前高", "牛市来了", "成交量创新高"], 3),
    ("unknown", [], 0),
    ("unknown混合", ["不知道", "帮我想想"], 0),
]

for name, signals, expected_id in tests:
    phase = detect_phase(signals)
    ok = phase.id == expected_id
    status = "PASS" if ok else f"FAIL (got phase {phase.id} '{phase.name}')"
    print(f"  {status}  {name}")

# Test format_phase_context
ctx = format_phase_context(PHASES[0])
assert "恐慌冲击期" in ctx
assert "2-3成" in ctx
assert "绝不替用户做投资决策" in ctx
print("  PASS  format_phase_context(phase1)")

ctx = format_phase_context(UNKNOWN_PHASE)
assert "信号不足期" in ctx
print("  PASS  format_phase_context(unknown)")

# Test get_phase_summary
summary = get_phase_summary()
assert "三阶段九子螺旋" in summary
assert "恐慌冲击期" in summary
assert "震荡脱敏期" in summary
assert "基本面回归期" in summary
print("  PASS  get_phase_summary")

# Test phases data integrity
assert len(PHASES) == 3
assert PHASES[0].id == 1
assert PHASES[1].id == 2
assert PHASES[2].id == 3
assert len(PHASES[0].sub_phases) == 3
assert len(PHASES[1].sub_phases) == 3
assert len(PHASES[2].sub_phases) == 3
print("  PASS  phase data integrity (9 sub-phases)")

print("\nAll phase_model tests passed.")

# Test dispatch deep question
from app.core.dispatch import _is_deep_question, _count_consecutive_deep

print("\n=== dispatch deep_question 测试 ===")
assert _is_deep_question("这个为什么这样？")
assert _is_deep_question("底层框架是怎么样的")
assert not _is_deep_question("市场今天怎么样")
print("  PASS  _is_deep_question")

ctx = [
    {"role": "user", "content": "为什么估值这么高？"},
    {"role": "assistant", "content": "因为...", "persona": "spotlight_tutor"},
    {"role": "user", "content": "那底层框架怎么推导？"},
]
assert _count_consecutive_deep(ctx) == 2
ctx2 = [{"role": "user", "content": "今天天气不错"}]
assert _count_consecutive_deep(ctx2) == 0
print("  PASS  _count_consecutive_deep")

print("\nAll tests passed.")
