import sys
sys.path.insert(0, "/Users/tao/my-node-project/lighthouse/lighthouse-app/backend")

from app.core.dispatch import dispatch, Persona, UserState

tests = [
    ("UNKNOWN_RAW → IGNITER", "你好", {"type": "UNKNOWN_RAW"}, [], Persona.IGNITER, None),
    ("UNKNOWN_RAW handoff → DEEP_MIRROR + ASSESSED", "嗯有过",
     {"type": "UNKNOWN_RAW"},
     [{"role": "assistant", "content": "...", "persona": "igniter"}],
     Persona.DEEP_MIRROR, UserState.UNKNOWN_ASSESSED),
    ("UNKNOWN_ASSESSED → DEEP_MIRROR", "我想了解估值",
     {"type": "UNKNOWN_ASSESSED"}, [], Persona.DEEP_MIRROR, None),
    ("UNKNOWN_ASSESSED + 帮我分析 → EXECUTOR", "帮我分析一下茅台",
     {"type": "UNKNOWN_ASSESSED"}, [], Persona.EXECUTOR, None),
    ("BUILDER default → DEEP_MIRROR", "最近市场怎么看",
     {"type": "BUILDER"}, [], Persona.DEEP_MIRROR, None),
    ("BUILDER + 陪学 → SPOTLIGHT_TUTOR", "陪我学一下",
     {"type": "BUILDER"}, [], Persona.SPOTLIGHT_TUTOR, None),
    ("BUILDER + 帮我整理 → EXECUTOR", "帮我整理数据",
     {"type": "BUILDER"}, [], Persona.EXECUTOR, None),
    ("Reset → IGNITER + UNKNOWN_RAW", "随便聊聊",
     {"type": "BUILDER"}, [], Persona.IGNITER, UserState.UNKNOWN_RAW),
    ("USER default → DEEP_MIRROR", "市场怎么样",
     {"type": "USER"}, [], Persona.DEEP_MIRROR, None),
    ("USER + 帮我查 → EXECUTOR", "帮我查一下茅台PE",
     {"type": "USER"}, [], Persona.EXECUTOR, None),
    ("HYBRID default → DEEP_MIRROR", "有什么推荐吗",
     {"type": "HYBRID"}, [], Persona.DEEP_MIRROR, None),
    ("喘口气 → IGNITER reset", "喘口气",
     {"type": "BUILDER"}, [], Persona.IGNITER, UserState.UNKNOWN_RAW),
]

passed = 0
failed = 0
for name, user_input, state, ctx, exp_persona, exp_state in tests:
    r = dispatch(user_input, state, ctx)
    ok = r.persona == exp_persona
    if exp_state:
        ok = ok and r.next_state == exp_state
    if ok:
        print(f"  PASS  {name}")
        passed += 1
    else:
        print(f"  FAIL  {name}: got persona={r.persona.value} next_state={r.next_state}, expected persona={exp_persona.value} next_state={exp_state}")
        failed += 1

print(f"\n{passed}/{passed+failed} tests passed")
if failed:
    sys.exit(1)
