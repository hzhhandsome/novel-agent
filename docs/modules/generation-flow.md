# 章节生成流程模块

## 模块职责

章节生成流程负责把项目上下文转换为章节候选稿，并记录生成过程、审核结果和可恢复状态。

第一版要求是“简单可用的自动化小说生成闭环”，所以本模块必须保持 LangGraph 节点化编排，不能退化成一个固定大函数。

## 入口文件

- `backend/app/agent/chapter_graph.py`：章节生成 LangGraph。
- `backend/app/services/chapter_service.py`：生成、重试、采纳、拒绝的服务入口。
- `backend/app/api/routes/generation.py`：章节生成和任务恢复 API。
- `backend/app/api/routes/chapters.py`：章节保存、采纳、拒绝 API。

## 核心流程

当前章节生成节点顺序：

1. `load_context`：读取项目、章节、角色时期卡、事件时间线、世界观规则、伏笔、灵感、前文摘要，先通过 RAG 召回相关旧信息，再通过规则式上下文预算决定实际进入 prompt 的可变上下文。
2. `build_chapter_target`：确定本章目标。
3. `build_prompt_package`：组装提示包。
4. `generate_prose`：调用模型生成正文候选。
5. `audit_prose`：调用模型审核正文候选是否偏离目标、主线、人设、世界观和前文。
6. `summarize_chapter`：审核后生成正式候选摘要，避免把未审核正文先固化进上下文。
7. `judge_foreshadowing`：判断伏笔新增、推进、回收和提前泄露。
8. `judge_character_period`：判断角色时期卡更新、新建和阶段变化。
9. `propose_future_plan_updates`：根据本章实际正文判断后续章节标题和线路是否需要调整。
10. `build_candidate_result`：汇总正文、摘要、审核、伏笔、角色卡和后续线路建议。
11. `persist_candidate_result`：保存候选正文、候选摘要、审核发现、任务状态和节点快照。

`persist_candidate_result` 只保存候选结果和过程，不自动把候选正文采纳为正式正文，也不直接修改正式角色卡、事件时间线、世界观规则、伏笔表或后续章节标题。正式采纳仍由章节采纳流程负责。

`judge_character_period` 属于非关键判断节点。真实 LLM 返回非法 JSON 时，该节点记录 `skipped=true` 和错误信息，并输出空角色变化结果，让章节正文、摘要、审核、伏笔和候选保存继续完成。正文生成、审核、摘要和候选保存仍保持严格失败策略。

### 上下文预算

`load_context` 先完整读取正式上下文，再对可变上下文做规则式预算裁剪。核心设定和角色当前时期保留在固定上下文中；章节摘要、事件时间线、作者灵感、伏笔和世界观规则按分区预算进入最终 prompt。

当前第一阶段使用字符数作为粗略预算单位：

- `chapter_summaries`：优先保留最近章节摘要。
- `story_events`：优先保留最近写入的事件。
- `inspirations`：优先保留最新未应用灵感。
- `foreshadowing_items`：保留预算内伏笔条目。
- `world_rules`：保留预算内世界观规则。

预算报告写入 `context_package.context_budget`，包含总预算、各分区已用量、纳入数量、裁剪数量和被裁剪内容摘要。Agent 后台上下文视图应展示该报告，方便排查章节增多后的幻觉来源。当前预算器会保证每个非空分区至少保留一条内容；RAG 检索结果会先调整候选优先级，再由预算器决定是否进入 prompt。

### RAG 召回

`load_context` 会从正式记忆构建向量检索文档，并根据本章查询召回相关旧信息。检索来源包括已采纳章节摘要、事件时间线、世界观规则、角色时期卡和伏笔条目。检索报告写入 `context_package.retrieval_results`，前端 Agent 后台在“上下文”tab 展示后端类型、查询和命中内容。

Docker 运行时使用 Qdrant 和本地 `sentence-transformers` embedding；测试和本地默认使用 hash embedding。候选正文和候选摘要不进入检索文档，避免污染正式记忆。

### SSE 进度输出

`POST /api/chapters/{chapter_id}/generate/stream` 返回 `text/event-stream`，用于前端实时显示节点进度。

事件：

- `task`：包含完整 `GenerationTask` 快照，前端用其中的 11 个 `GenerationTaskStep.status` 更新节点进度。
- `done`：表示本次流结束。

前端固定展示 11 个中文节点，不兼容旧 6 节点流程；后端节点名只作为状态映射键。节点状态展示规则：

- `completed`：显示完成勾选。
- `running`：显示执行中。
- `failed`：显示失败。
- 未返回对应节点步骤：显示等待。

当前第一版不做 token 级逐字正文流。前端使用同一条任务 SSE：

- 后台用所有 `GenerationTaskStep.status` 更新 11 个节点进度。
- 中部正文区在 `generate_prose.output_snapshot.generated_content` 出现后，立即写入章节正文 textarea，作为当前候选正文展示。
- `persist_candidate_result` 完成后再刷新项目数据，保持候选正文和数据库状态一致。

生成期间正文 textarea、小说想法、作者灵感、模型配置和生成控制必须禁用，避免用户在提示包、生成结果和候选保存尚未稳定时修改上下文。候选正文的采纳和拒绝入口放在正文工具栏，不再使用独立“生成结果”展示块。

### 指定章数全自动生成

`POST /api/projects/{project_id}/auto-generate/stream` 返回 `text/event-stream`。

外层任务 `kind` 为 `auto_chapter_generation`，负责记录目标章数、已完成章数、当前章节任务、已自动采纳章节和暂停/失败原因。当前章节仍通过子 `chapter_generation` 任务展示 11 节点进度。

全自动生成只负责循环控制：

- 找到下一章；如果不存在则创建占位章节。
- 运行现有单章 11 节点生成流程。
- 检查 `audit_prose` 是否存在阻塞审核发现。
- 无阻塞时复用采纳流程，把候选正文转为正式正文。
- 达到指定章数后停止。

如果审核存在阻塞问题，外层任务进入 `paused`，不自动采纳当前章节。模型、节点或数据库失败时，外层任务进入 `failed`，保留当前子任务和错误原因。

## 数据和状态

关键模型：

- `GenerationTask`：一次生成任务。
- `GenerationTaskStep`：节点级步骤状态。
- `GenerationRun`：生成记录，包括提示包、输出、审核结果、是否采纳。
- `auto_chapter_generation`：全自动外层任务类型，复用 `GenerationTask` 记录总进度。
- `Chapter.generated_content`：生成候选稿。
- `Chapter.content`：正式采纳正文。
- `Chapter.summary`：后续章节使用的摘要。
- `Character.period_stage` / `period_summary`：角色当前时期卡的正式状态。
- `StoryEvent`：已采纳章节沉淀的事件时间线。
- `WorldRule`：项目世界观和已采纳章节沉淀的规则约束。
- `context_package.retrieval_results`：本次 `load_context` 的 RAG 召回报告，包含后端、查询、命中来源、分数和文本。
- `context_package.context_budget`：本次 `load_context` 的上下文预算报告，只描述可变上下文分区的预算使用和裁剪结果。
- `GenerationTask.model_config_snapshot`：任务创建时的模型配置快照，用于生成和重试复现。
- `GenerationRun.model_config_snapshot`：采纳或拒绝时保存的模型配置快照，用于后续回看。

任务状态用于中断恢复，不应只依赖内存。前端 Agent 后台应优先读取 `GenerationTaskStep.output_snapshot` 展示真实节点输出；没有任务时才显示目标流程占位。

章节采纳后，`accept_chapter_candidate` 会把正式正文、生成记录和结构化记忆一起提交：章节摘要生成事件时间线，章节摘要生成世界观/剧情约束记录，`judge_character_period` 的结果更新角色时期摘要和来源章节。全自动生成也必须复用该采纳路径。

## 扩展点

后续可添加：

- 用户输入审核节点。
- 自动修订节点。
- 节点级模型选择。
- 自动正式入库能力必须由明确的全自动任务控制，并复用采纳流程；`persist_candidate_result` 仍不得直接写正式正文。
- 更细粒度的摘要、伏笔、角色时期卡、事件、世界规则和后续线路确认。

新增节点时必须同步更新任务步骤记录和相关测试。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_chapter_generation.py backend/tests/test_generation_recovery.py -v
```

全量后端验证：

```powershell
python -m pytest -v
```

## 后续修改注意事项

- 不要绕过 LangGraph 直接在服务层拼接完整生成流程。
- 生成任务必须记录每个关键节点的状态。
- 模型调用失败时要保留可展示的失败原因。
- 采纳后才应把候选稿转为正式正文，并写入正式结构化记忆。
- `persist_candidate_result` 不是自动采纳，不得绕过采纳边界直接污染正式上下文或结构化记忆。
- 全自动生成只能作为外层任务循环复用单章 LangGraph，不要把多个章节的生成逻辑写成不可恢复的大函数。
- 后续输入锁定、AI 输入评判、LLM 切换都需要考虑当前任务状态和生成记录复现。
- 调整上下文来源或新增可变记忆实体时，必须同步检查 RAG 检索来源和上下文预算分区，避免新增内容绕过预算直接进入 prompt。
- 生成和重试必须使用任务创建时的 `model_config_snapshot`，不要在任务中途重新读取当前全局模型配置。
