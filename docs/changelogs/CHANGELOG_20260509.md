# 改动地图 - 2026年05月09日

## 本次需求关联
- 对应需求：技术方案 v0.3 · 对话引擎 + 用户画像引擎 + 日志系统 + 记忆折叠
- 需求简述：后端骨架搭建完成，三大模块就绪，等待三方联调

## 文件变更清单
| 文件路径 | 改动类型 | 功能点描述（人类语言） | 关联需求 |
|:---|:---|:---|:---|
| backend/app/core/deepseek.py | 新增 | DeepSeek API 客户端：SSE 流式调用、4 种人格 System Prompt（引信/深度镜/执行手/陪学） | 对话引擎接入 AI |
| backend/app/api/v1/chat.py | 修改 | 接入 dispatch 面孔切换 + 三阶段模型注入 + 记忆折叠上下文 + SSE 输出 persona 标记 | 对话引擎·调度集成 |
| backend/app/core/memory_folding.py | 新增 | 记忆折叠：对话超 50 条自动折叠为认知增量摘要，支持手动/归档触发 | 日志系统·记忆折叠 |
| backend/app/models/__init__.py | 修改 | 新增 SessionSummary 模型（session_summaries 表） | 记忆折叠·数据持久化 |
| backend/init.sql | 修改 | 新增 session_summaries 表 + 索引 | 数据库扩展 |
| backend/app/api/v1/user.py | 修改 | 用户画像引擎完整实现：前置判定三问 + builder/user/hybrid 类型判定 + 五态迁移 | 用户画像引擎 |
| backend/app/api/v1/log.py | 修改 | 日志系统写库：系统日志 / 用户反馈日志双向写入 PostgreSQL | 日志系统 |
| backend/app/config.py | 修改 | config 路径从相对路径改为绝对路径，支持从项目根目录读取 .env | 环境配置 |

## 依赖变更（如有）
- 无

## 数据库/配置变更（如有）
- 新增 `session_summaries` 表（session_id, summary_text, message_count, fold_type, created_at）
- `.env` 从 `backend/` 移到了项目根目录 `lighthouse-app/.env`
