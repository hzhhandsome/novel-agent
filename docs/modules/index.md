# 模块文档索引

模块文档只维护稳定且容易出错的大模块。普通小功能不强制新增模块文档，具体设计和实施计划由 AI 使用 superpowers 流程处理。

## 当前模块

| 模块 | 文档 | 主要入口 | 什么时候必须先读 |
| --- | --- | --- | --- |
| 章节生成流程 | `docs/modules/generation-flow.md` | `backend/app/agent/chapter_graph.py` | 改 LangGraph 节点、生成任务、审核、摘要、中断恢复 |
| 模型提供器 | `docs/modules/model-provider.md` | `backend/app/services/model_provider.py` | 改 LLM 接入、模型切换、模型配置、模型调用记录 |
| 结构化记忆 | `docs/modules/memory-system.md` | `backend/app/models/memory.py` | 改角色时期、事件时间线、世界观规则、正式记忆写入或上下文记忆加载 |
| 检索召回 | `docs/modules/retrieval.md` | `backend/app/services/vector_memory.py` | 改 RAG、向量库、embedding、检索来源、召回结果和上下文预算接入 |
| 评测 | `docs/modules/evaluation.md` | `backend/app/services/evaluation.py` | 改摘要事实保留率、审核冲突检出率、gold case、评测 runner |
| 作者交互 | `docs/modules/author-interaction.md` | `backend/app/services/input_review.py` | 改用户输入评判、作者灵感写入前检查、正文修改前检查 |
| 训练数据准备 | `docs/modules/training-data.md` | `backend/app/services/training_data.py` | 改微调数据导出、JSONL 样本格式、采纳/拒绝样本边界 |

## 文档粒度

模块文档应该写清：

- 模块职责。
- 入口文件。
- 核心流程。
- 关键数据和状态。
- 扩展点。
- 测试方式。
- 后续修改注意事项。

模块文档不写每次开发流水账。一次具体功能怎么实现，由 AI 在 superpowers 计划中处理，用户不需要维护。

## 新增模块文档条件

满足任一条件时再新增模块文档：

- 模块有稳定职责，后续会反复修改。
- 模块涉及跨前后端、数据库或外部服务。
- 模块有状态机、任务流或复杂数据流。
- 模块有容易被后续开发破坏的关键约束。

当前暂不为小前端组件、单个 API 或一次性脚本单独写模块文档。
