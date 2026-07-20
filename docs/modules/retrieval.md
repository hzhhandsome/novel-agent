# 检索召回模块

## 模块职责

检索召回模块负责在章节生成前，从正式记忆中找出和当前章节最相关的旧信息，减少长篇生成时只靠最近摘要导致的遗忘和幻觉。

当前第一阶段是向量 RAG：

- Docker 运行使用 Qdrant 作为向量数据库。
- Docker 后端使用本地免费 embedding 模型 `BAAI/bge-small-zh-v1.5`。
- 测试和本地默认使用确定性的 hash embedding，不依赖网络下载模型。
- 检索结果进入上下文预算器，由预算器决定最终进入 prompt 的内容。
- 已有内置 RAG Eval 第一阶段，用固定 gold retrieval report 评测 `recall@k`、`precision@k`、`hit_rate@k` 和 `MRR`。

## 入口文件

- `backend/app/services/embeddings.py`：embedding provider。
- `backend/app/services/vector_memory.py`：本地向量检索和 Qdrant 检索。
- `backend/app/evals/rag_cases.py`：固定 RAG 召回评测样例。
- `backend/app/agent/chapter_graph.py`：`load_context` 构建查询、正式记忆文档并调用检索。
- `frontend/src/components/AgentWorkspace.tsx`：Agent 后台展示 RAG 召回报告。
- `docker-compose.yml`：Qdrant 服务和后端检索环境变量。

## 核心流程

1. `load_context` 读取项目正式上下文。
2. 构建检索查询：当前章节标题、小说定位、世界观、主线、角色时期卡和作者灵感。
3. 构建正式记忆文档：
   - 已采纳章节摘要。
   - 事件时间线。
   - 世界观规则。
   - 角色时期卡。
   - 伏笔条目。
4. 根据配置选择检索后端：
   - `local`：用 hash embedding 在进程内排序，主要用于测试和轻量本地运行。
   - `qdrant`：把正式记忆 upsert 到 Qdrant，再按 `project_id` 过滤召回 top K。
   - `disabled`：关闭检索，只保留上下文预算。
5. 检索命中的候选优先进入上下文预算排序。
6. `context_package.retrieval_results` 记录后端、查询、命中来源、分数和文本，供 Agent 后台调试。
7. 内置 Eval 使用固定 retrieval report 验证“应该召回的旧信息是否出现在 top k”，用于后续比较 query、chunk、混合检索和 reranker 策略。

## 数据和状态

检索文档不新增业务数据库表。向量点的稳定 id 由 `project_id/source/source_id` 生成，保证重复 upsert 不产生重复数据。

Qdrant payload 包含：

- `project_id`
- `source`
- `source_id`
- `text`
- `metadata`

正式记忆边界：

- 候选正文和候选摘要不进入向量检索。
- 只有已采纳章节、正式结构化记忆、角色卡和伏笔会被构建为检索文档。
- 全自动生成复用采纳路径，下一章生成时即可召回上一章采纳后的正式记忆。

## 配置项

```powershell
NOVEL_AGENT_RETRIEVAL_BACKEND=local|qdrant|disabled
NOVEL_AGENT_RETRIEVAL_TOP_K=8
NOVEL_AGENT_QDRANT_URL=http://qdrant:6333
NOVEL_AGENT_QDRANT_COLLECTION=novel_agent_memory
NOVEL_AGENT_EMBEDDING_PROVIDER=hash|sentence_transformers
NOVEL_AGENT_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
NOVEL_AGENT_EMBEDDING_DIMENSION=384
```

## 扩展点

后续可以增加：

- 专门的索引重建 API。
- embedding 批处理和后台任务。
- 混合检索：关键词 + 向量。
- 重排模型。
- 基于真实检索日志的在线 recall@k、MRR、命中覆盖率 eval。
- 地点、物品、阵营等更多结构化实体。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_retrieval.py backend/tests/test_context_budget.py -v
npm test -- --run src/App.test.tsx
```

全量验证：

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

## 后续修改注意事项

- 不要把候选正文直接写入向量库。
- 新增检索来源后，必须明确它是否是正式记忆，并同步上下文预算分区。
- Qdrant 失败不能阻塞基础生成；当前实现会回退到本地向量排序。
- 更换 embedding 模型时必须同步 `NOVEL_AGENT_EMBEDDING_DIMENSION`。

## 2026-07-19 更新

- Agent 后台顶部常驻显示本次 `load_context.context_budget` 的占用摘要，方便判断长篇生成时上下文是否接近预算上限。
- RAG 召回结果仍在“上下文”tab 和 `load_context` 节点详情中展示；召回结果只影响候选优先级，最终是否进入 prompt 仍由上下文预算决定。

## 2026-07-20 更新

- 新增内置 RAG Eval 第一阶段：使用固定 retrieval report 计算 `recall@k`、`precision@k`、`hit_rate@k` 和 `MRR`。
- 该评测不读取真实项目数据库，也不调用 Qdrant；它用于稳定比较后续检索策略变更。
- 真实检索日志评测、混合检索和 reranker 对比仍是后续扩展。
