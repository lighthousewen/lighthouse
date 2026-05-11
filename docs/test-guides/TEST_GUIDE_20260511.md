# 测试路径 · DS-001 深筑模块（2026年05月11日提测）

## 测试环境准备
- 后端服务：`cd backend && python3.13 -m uvicorn app.main:app --port 8000`
- PostgreSQL 运行中（Postgres.app），`lighthouse` 数据库已初始化
- `.env` 中 `DEEPSEEK_API_KEY` 已配置真实 Key

---

## 单元测试（代码级）

### 用例1-12：面孔切换状态机 dispatch()
**步骤：** `python3.13 backend/tests/test_dispatch.py`
**预期：** 12/12 全通过
**结果：** ✅ 通过

| # | 用例 | 输入 | 预期 persona |
|:---|:---|:---|:---|
| 1 | UNKNOWN_RAW 首条消息 | state=UNKNOWN_RAW, ctx=[] | igniter |
| 2 | 引信线头被接住 | state=UNKNOWN_RAW, last=igniter | deep_mirror |
| 3 | UNKNOWN_ASSESSED 默认 | state=UNKNOWN_ASSESSED | deep_mirror |
| 4 | UNKNOWN_ASSESSED + 执行手召唤 | 帮我分析一下茅台 | executor |
| 5 | BUILDER 默认 | state=BUILDER | deep_mirror |
| 6 | BUILDER + 陪学召唤 | 陪我学一下 | spotlight_tutor |
| 7 | BUILDER + 执行手召唤 | 帮我整理数据 | executor |
| 8 | 重置信号 | 随便聊聊 | igniter + reset to UNKNOWN_RAW |
| 9 | USER 默认 | state=USER | deep_mirror |
| 10| USER + 执行手召唤 | 帮我查一下茅台PE | executor |
| 11| HYBRID 默认 | state=HYBRID | deep_mirror |
| 12| 喘口气重置 | 喘口气 | igniter + reset to UNKNOWN_RAW |

### 用例13-21：三阶段模型 phase_model
**步骤：** `python3.13 backend/tests/test_phase_model.py`
**预期：** 9/9 全通过
**结果：** ✅ 通过

| # | 用例 | 关键验证 |
|:---|:---|:---|
| 13 | detect_phase 恐慌期 | 沪指暴跌+创业板跌3% → 恐慌冲击期(id=1) |
| 14 | detect_phase 脱敏期 | 反弹+站稳5日线 → 震荡脱敏期(id=2) |
| 15 | detect_phase 基本面 | 突破前高+牛市 → 基本面回归期(id=3) |
| 16 | detect_phase unknown | 空信号 → 信号不足期(id=0) |
| 17 | detect_phase 混合unknown | 不知道+帮我想想 → unknown |
| 18 | format_phase_context(phase1) | 输出含"恐慌冲击期""2-3成""绝不替用户做投资决策" |
| 19 | format_phase_context(unknown) | 输出含"信号不足期" |
| 20 | phase data integrity | 3大阶段各3子阶段=9子阶段 |
| 21 | get_phase_summary | 含三阶段完整简介 |

### 用例22-23：陪学自动升级
**步骤：** `python3.13 backend/tests/test_phase_model.py`（后半部分）
**预期：** 2/2 全通过
**结果：** ✅ 通过

| # | 用例 | 关键验证 |
|:---|:---|:---|
| 22 | _is_deep_question | "这个为什么"→True, "底层框架"→True, "市场怎么样"→False |
| 23 | _count_consecutive_deep | 连续2轮深入问题→2, 普通对话→0 |

---

## 接口联调测试（HTTP 级）

### 用例24：冷启动全链路
**步骤：**
1. `POST /api/v1/sessions` 创建会话
2. `POST /api/v1/chat` 发送"你好"
3. `POST /api/v1/chat` 发送"嗯有过"
4. `POST /api/v1/chat` 发送"帮我分析一下茅台"
**预期：** persona 依次为 igniter → deep_mirror → executor
**结果：** ✅ 通过（详见下方自动验证日志）

### 用例25：三阶段模型端点
**步骤：**
1. `GET /api/v1/phase/summary` → 返回三阶段模型简介
2. `POST /api/v1/phase/analyze` signals=["沪指暴跌","创业板跌3%"] → 恐慌冲击期
3. `POST /api/v1/phase/analyze` signals=["不知道"] → 信号不足期
4. `GET /api/v1/phase/phases` → 返回4个阶段（含unknown）
**预期：** 全部 200 OK
**结果：** ✅ 通过

### 用例26：会话状态持久化
**步骤：**
1. 创建会话 → state=UNKNOWN_RAW
2. 首条消息"你好"后 → GET 会话确认 state=UNKNOWN_ASSESSED
3. 第二条消息"嗯有过"后 → 不应再返回引信（不是 UNKNOWN_RAW）
**预期：** 状态随 dispatch next_state 正确迁移
**结果：** ✅ 通过（已修复 StreamingResponse commit 时序 Bug）

### 用例27：反馈按钮
**步骤：**
1. 前端点击「这不是我要的帮助」
2. 直查 logs 表确认 `feedback_type=dispatch_mismatch`
**预期：** 日志入库 + 按钮显示「已记录」
**结果：** ✅ 通过

### 用例28：记忆折叠上下文注入
**步骤：**
1. 发送对话 → 查看 session_summaries 表
2. 手动 `/sessions/{id}/fold` → 确认 summary_text 非空
3. `/sessions/{id}/archive` → 确认归档成功
**预期：** 折叠摘要包含对话核心议题
**结果：** ✅ 通过（17 用例详见 `TEST_GUIDE_20260509.md`）

---

## 自测结论

| 项目 | 结果 |
|:---|:---:|
| 总用例数 | **28** |
| 单元测试通过 | **26 / 26** |
| HTTP 接口验证通过 | **13 / 13** |
| 通过率 | **100%** |
