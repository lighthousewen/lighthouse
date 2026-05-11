# 改动地图 - 2026年05月11日

## 本次需求关联
- 对应需求：技术方案 v0.3 · 面孔切换状态机 / 陪学模式 / 三阶段模型 / 反馈通道
- 需求简述：MVP 全模块完成，提交品质部（淬镜）审查

## 本轮改动范围（05-09 → 05-11 三人汇总）

### DS-001 深筑

| 文件路径 | 改动类型 | 功能点描述 | 关联需求 |
|:---|:---|:---|:---|
| backend/app/core/dispatch.py | 新增 | 面孔切换六状态机：IGNITER/DEEP_MIRROR/EXECUTOR/SPOTLIGHT_TUTOR/SPOTLIGHT_ASK + 四步试探法信号检测 + 陪学自动升级触发器 | Week 2 面孔切换 |
| backend/app/core/phase_model.py | 新增 | 三阶段九子螺旋硬编码规则表（3×3子阶段）+ unknown信号不足期 + detect_phase()关键词匹配 + format_phase_context() Prompt注入 | Week 3 三阶段模型 |
| backend/app/api/v1/phase.py | 新增 | /api/v1/phase 端点：summary / analyze / phases | Week 3 三阶段模型 |
| backend/app/api/internal.py | 新增 | /api/internal/dispatch 端点 | Week 2 接口契约 |
| backend/app/core/deepseek.py | 重写 | SOUL正式System Prompt替换占位：引信(深研)/深度镜(DS-000)/执行手(DS-001)/陪学(DS-003)/追问(DS-002) + extra_context参数 | Week 2 SOUL集成 |
| backend/app/api/v1/chat.py | 改造 | dispatch()动态persona决策 + session.state自动迁移 + 三阶段上下文注入 + 记忆折叠上下文 + 状态持久化hotfix | Week 2/3 集成 |
| backend/app/main.py | 修改 | 注册 internal / phase 路由 |
| frontend/src/components/FeedbackButton.tsx | 修改 | 新增三态反馈（idle/sending/done），点击后显示「已记录」 | 联调反馈修复 |
| frontend/src/components/ChatWindow.tsx | 修改 | onFeedback 类型同步 | 联调修复 |

### BE-001 程远

| 文件路径 | 改动类型 | 功能点描述 | 关联需求 |
|:---|:---|:---|:---|
| backend/app/core/memory_folding.py | 新增 | 记忆折叠：DeepSeek认知增量摘要 + 自动/手动/归档折叠 + 摘要注入 | Week 3 日志系统 |
| backend/app/api/v1/user.py | 修改 | 前置判定三问（DS-004建造者版）+ 五态状态机 + 类型判定 | Week 2 用户画像 |
| backend/app/api/v1/log.py | 修改 | 系统/用户反馈日志写库 | Week 2 日志 |
| backend/app/models/__init__.py | 修改 | 新增 UserProfile / AssessmentAnswer / Log / SessionSummary 模型 | 数据层扩展 |
| backend/init.sql | 修改 | 新增四张表 + 索引 | DB schema |

### FE-001 映初

| 文件路径 | 改动类型 | 功能点描述 | 关联需求 |
|:---|:---|:---|:---|
| frontend/src/hooks/useSSE.ts | 修改 | onChunk从(文字)改为(文字+persona双字段) | SSE流式 |
| frontend/src/App.tsx | 修改 | currentPersonaRef追踪面孔 + 反馈context_snapshot拼接近4条 | 对话界面 |
| frontend/src/components/MessageBubble.tsx | 修改 | persona→中文标签映射（引信/深度镜/执行手/陪学/追问） | 面孔标识 |
| frontend/src/App.css | 修改 | persona标签深色圆角badge | UI优化 |
| frontend/src/api/client.ts | 修改 | sendFeedback新增contextSnapshot参数 | 反馈增强 |

## 依赖变更
- 无（所有依赖在 Week 1 已固定）

## 数据库变更
- 新增：user_profiles / assessment_answers / logs / session_summaries 四张表
- DDL 已同步至 `backend/init.sql`
