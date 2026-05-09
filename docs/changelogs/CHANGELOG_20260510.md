# 改动地图 - 2026年05月10日

## 本次需求关联
- 对应需求：技术方案 v0.3 · 对话界面 + 反馈通道
- 需求简述：前端从 echo 占位切换为真实 SSE 流式渲染，反馈通道联调就绪

## 文件变更清单
| 文件路径 | 改动类型 | 功能点描述（人类语言） | 关联需求 |
|:---|:---|:---|:---|
| frontend/src/hooks/useSSE.ts | 修改 | `onChunk` 回调签名变更，将 `persona` 面孔字段从 SSE 数据传递到消息层 | 对话界面·多面渲染 |
| frontend/src/App.tsx | 修改 | 新增 `currentPersonaRef` 追踪当前发言面孔；`onChunk` 处理 `content` + `persona` 双字段 | 对话界面·面孔切换 |
| frontend/src/components/MessageBubble.tsx | 修改 | 新增面孔标签映射表（引信/深度镜/执行手/陪学/追问），气泡上方显示当前身份 | 对话界面·面孔标识 |
| frontend/src/App.css | 修改 | persona 标签样式增强：深色背景 + 圆角标签，视觉区分不同面孔 | 对话界面·UI 优化 |
| frontend/src/App.tsx | 修改 | `handleFeedback` 自动拼接最近 4 条对话上下文作为 `context_snapshot` 提交 | 反馈通道·上下文记录 |
| frontend/src/api/client.ts | 修改 | `sendFeedback` 新增 `contextSnapshot` 参数，日志记录更丰富 | 反馈通道·日志增强 |

## 依赖变更（如有）
- 无

## 数据库/配置变更（如有）
- 无
