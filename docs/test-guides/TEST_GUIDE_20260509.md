# 测试路径 - 2026年05月09日

## 测试环境准备
- 后端服务运行中：http://localhost:8000
- PostgreSQL 数据库运行中，`sessions`、`messages`、`user_profiles`、`assessment_answers`、`logs` 五张表已建
- `.env` 中 `DEEPSEEK_API_KEY` 已配置真实 Key

---

## 用例1：健康检查
**步骤：** `GET http://localhost:8000/health`
**预期：** 返回 `{"status": "ok", "version": "0.1.0"}`
**结果：** ✅ 通过

## 用例2：创建会话
**步骤：** `POST /api/v1/sessions`
**预期：** 返回 session_id + state="UNKNOWN_RAW"
**结果：** ✅ 通过 — `{"session_id": "86543...", "state": "UNKNOWN_RAW"}`

## 用例3：DeepSeek 流式对话
**步骤：** `POST /api/v1/chat` 发送"你好"
**预期：** SSE 流式返回 content 块 + 结尾 `{"done": true}`，不含错误消息
**结果：** ✅ 通过 — 22 个 content 块，done 标记存在，无错误

## 用例4：消息持久化
**步骤：** `GET /api/v1/sessions/{id}/messages`
**预期：** 返回该会话的消息列表，包含 user 和 assistant 角色
**结果：** ✅ 通过 — 消息已写入 `messages` 表

## 用例5：获取前置判定三问
**步骤：** `GET /api/v1/assessment/questions`
**预期：** 返回 3 个问题，每题有 A/B 选项
**结果：** ✅ 通过 — 三问完整返回

## 用例6：前置判定 — builder 类型（AAA）
**步骤：** `POST /api/v1/onboarding/assess` 三题全部选 A
**预期：** primary_type="builder", confidence=0.95, state="BUILDER"
**结果：** ✅ 通过

## 用例7：前置判定 — user 类型（BBB）
**步骤：** `POST /api/v1/onboarding/assess` 三题全部选 B
**预期：** primary_type="user", confidence=0.95, state="USER"
**结果：** ✅ 通过

## 用例8：前置判定 — hybrid 类型（ABA）
**步骤：** `POST /api/v1/onboarding/assess` 2A1B
**预期：** primary_type="builder", confidence=0.65, state="BUILDER"
**结果：** ✅ 通过 — 2A1B → builder 0.65

## 用例9：获取用户画像
**步骤：** `GET /api/v1/user/{id}`
**预期：** 返回完整的 UserProfile，含 assessment_done=true
**结果：** ✅ 通过

## 用例10：状态迁移
**步骤：** `PUT /api/v1/user/{id}/state?state=UNKNOWN_ASSESSED`
**预期：** 状态更新成功，再次 GET 确认
**结果：** ✅ 通过 — USER → UNKNOWN_ASSESSED 迁移成功

## 用例11：非法状态拒绝
**步骤：** `PUT /api/v1/user/{id}/state?state=INVALID`
**预期：** 返回 400，提示合法状态列表
**结果：** ✅ 通过 — 正确拒绝并列出可选状态

## 用例12：未知用户自动创建
**步骤：** `GET /api/v1/user/{不存在id}`
**预期：** 自动创建用户，state=UNKNOWN_RAW，assessment_done=false
**结果：** ✅ 通过

## 用例13：日志系统
**步骤：** `POST /api/v1/log/system` + `POST /api/v1/log/user`
**预期：** 返回 `{"status": "logged"}`
**结果：** ✅ 通过

## 用例14：数据库持久化验证
**步骤：** psql 直查 messages、logs、user_profiles 表
**预期：** 数据已写入对应表中
**结果：** ✅ 通过 — 所有表数据完整

---

## 自测结论

| 项目 | 结果 |
|:---|:---:|
| 总用例数 | 14 |
| 通过 | **14** |
| 失败 | **0** |

**备注：** 自测过程中发现 `event_stream` 中 `db.flush()` 在 `yield done` 之后执行可能导致持久化不完整，已修复（flush 移到 yield 之前）。
