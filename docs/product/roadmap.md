# 产品需求池

本文档维护后续需求池和优先级。进入开发前，从这里选取一个小范围需求；具体设计和实施计划由 AI 使用 superpowers 流程生成，用户不需要阅读或维护这些过程文档。

## 当前阶段

第一版已经进入手动验收阶段。后续开发优先围绕“让创作闭环更稳定、更可控”推进。

## P0

### Agent 实习/工作面试核心能力补强

状态：

- 已完成基础 Agent 闭环：LangGraph 节点编排、任务/节点持久化、SSE、上下文预算、结构化记忆、RAG、基础 Eval、模型切换/路由、token/cost 估算、微调数据准备。
- 面试和实习岗位还缺少更能体现“生产级 Agent 工程”的能力：混合检索、tokenizer 级上下文预算和用户反馈闭环。

目标：

- 把项目从“能跑的 LLM 应用”提升为“可观测、可评测、可恢复、可扩展工具能力的 Agent 系统”。
- 后续 P0 开发优先选择能直接支撑面试表达的能力，优先处理剩余的混合检索、tokenizer 级上下文预算和用户反馈闭环。

优先级建议：

1. 混合检索 + reranker。
2. tokenizer 级上下文预算。
3. 用户反馈数据闭环。

使用规则：

- 每次只选一个小 P0 独立设计和开发。
- 如果涉及已有模块，开发前必须先读对应 `docs/modules/` 文档。
- 新增稳定模块时再补 `docs/modules/<module-name>.md`，不要为一次性脚本单独建模块文档。

### Tool Calling / MCP 工具层

状态：

- 当前项目的 Agent 主要是固定 LangGraph 节点流程，LLM 通过节点调用模型或业务函数。
- 还没有统一 Tool Registry、tool schema、工具调用参数校验、工具调用审计，也没有 MCP server/client 适配。

目标：

- 增加一个受控工具层，让 Agent 可以在节点内调用项目内部工具，而不是只能依赖预先写死的上下文。
- 工具调用必须有 schema、参数校验、权限边界、调用记录、失败记录和耗时统计。
- 工具不能直接污染正式数据库；涉及记忆更新时只能返回候选结果，正式写入仍走采纳路径。

第一阶段建议：

- 新增内部 `ToolRegistry`，先不直接接复杂 MCP。
- 提供 3-5 个项目内工具：
  - `search_memory(query, project_id)`：检索正式记忆。
  - `get_chapter_summary(chapter_id)`：读取章节摘要。
  - `list_open_foreshadowing(project_id)`：读取未回收/推进中的伏笔。
  - `get_character_state(project_id, character_name)`：读取角色当前时期卡。
  - `propose_memory_update(...)`：返回候选记忆更新，不直接写正式表。
- 每次工具调用记录：task、step、tool_name、arguments、result 摘要、status、error、duration_ms。
- 后续再适配 MCP，把这些内部工具暴露为 MCP tools 或接入外部 MCP server。

验收方式：

- 后台能看到某个节点调用了哪些工具、参数是什么、返回了什么摘要、是否失败。
- 工具参数非法时不会调用业务逻辑。
- 工具失败不会让已完成节点状态丢失。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/retrieval.md`
- 后续可新增 `docs/modules/tool-calling.md`

### Agent Observability / Trace

状态：

- 当前已有 `GenerationTask`、`GenerationTaskStep.input_snapshot/output_snapshot`、模型 usage 和 Agent 后台节点展示。
- 这属于可观测基础，但还不是完整 trace：没有统一 trace_id/span_id，也没有把 LLM call、RAG call、tool call 串成一棵 trace tree。

目标：

- 为每次 Agent 运行建立可追踪的 trace，覆盖任务、节点、LLM 调用、RAG 检索、工具调用、usage、错误和耗时。
- 支持面试中讲清楚：一次生成为什么慢、哪里失败、用了哪些上下文、调用了哪些工具、成本是多少。

第一阶段建议：

- `GenerationTask` 增加或派生 `trace_id`。
- 每个 `GenerationTaskStep` 视为一个 span。
- LLM 调用、RAG 检索、Tool Calling 作为子 span 或独立 trace event 记录。
- 前端 Agent 后台增加“Trace”视图，按树状展示：
  - task
  - step
  - llm_call
  - retrieval
  - tool_call
  - persistence
- 暂不强依赖外部平台；后续可接 Langfuse、LangSmith 或 OpenTelemetry。

验收方式：

- 任意一次章节生成可以查看完整 trace。
- trace 中能看到每个节点耗时、模型、估算 token、检索 query、召回条数、工具调用结果和错误。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/model-provider.md`
- `docs/modules/retrieval.md`
- 后续可新增 `docs/modules/observability.md`

### RAG Eval：召回率、MRR 和命中覆盖率

状态：

- 已完成基础 RAG：Qdrant、本地 embedding、正式记忆召回、上下文预算接入、后台召回展示。
- 当前 Eval 只覆盖摘要事实保留率和审核冲突检出率，还没有证明 RAG 是否真的召回了该召回的旧信息。

目标：

- 建立 RAG 质量评测，不只证明“接了向量库”，还要证明“关键旧信息能被找回且排得靠前”。
- 支持比较不同 embedding、query 构造、chunk 策略、混合检索和 reranker 的效果。

指标：

- `recall@k`：应该召回的相关文档中，有多少出现在 top k。
- `precision@k`：top k 中有多少是真的相关文档。
- `MRR`：第一个相关结果排名的倒数。
- `hit_rate@k`：top k 是否至少命中一条相关文档。
- `packed_recall@k`：召回结果最终进入 prompt 的比例，避免“召回了但被预算裁掉”。

第一阶段建议：

- 新增 `backend/app/evals/rag_cases.py`，维护少量人工 gold case。
- 每个 case 包含：project fixture、query、expected source ids、top_k。
- 新增 RAG eval runner，输出 recall@k、precision@k、MRR、hit_rate。
- 前端 Eval 面板展示 RAG Eval 结果。

验收方式：

- 能运行固定 RAG gold cases。
- 修改 query 构造或检索策略后，可以比较指标变化。

涉及模块：

- `docs/modules/retrieval.md`
- `docs/modules/evaluation.md`

### Prompt 版本记录与 Eval 对比

状态：

- 当前已保存 prompt package 快照和模型配置快照。
- 还没有稳定的 prompt template version、prompt hash、context builder version，也不能按版本聚合 Eval。

目标：

- 每次生成任务保存实际使用的 prompt 模板版本、上下文构造版本、prompt hash 和关键参数。
- 支持回看某次生成为什么会得到当前结果。
- 支持比较不同 prompt 版本的生成质量、审核质量、RAG 使用效果和 Eval 指标。

第一阶段建议：

- 为每个节点 prompt 模板定义静态版本号，例如：
  - `generate_prose@2026-07-20.v1`
  - `audit_prose@2026-07-20.v1`
  - `summarize_chapter@2026-07-20.v1`
  - `judge_foreshadowing@2026-07-20.v1`
- `GenerationTaskStep.output_snapshot` 或独立字段保存：
  - `prompt_template`
  - `prompt_version`
  - `prompt_hash`
  - `context_builder_version`
- Eval runner 输出按 prompt_version 分组的结果。
- 第一阶段不做复杂 prompt 管理后台，只做记录、回看和指标分组。

验收方式：

- 任意生成记录能看到每个模型节点用的 prompt 版本。
- Eval 报告能按 prompt version 聚合，支持改 prompt 前后对比。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/model-provider.md`
- `docs/modules/evaluation.md`

### LLM-as-judge 语义评测

状态：

- 当前 Eval 是确定性文本匹配，稳定、便宜、可重复。
- 已完成轻量 LLM-as-judge 第一阶段：内置 Eval 可通过固定 judge case 和 rubric 输出语义评分、阻塞发现和理由，前端 Eval 面板可展示结果。
- 当前 judge 只作为离线评测工具，不插入章节生成 11 节点流程，也不写数据库历史。

目标：

- 增加可版本化的 LLM judge，用 rubric 评估复杂语义质量。
- LLM judge 只作为辅助评测，不替代确定性 gold case 和人工抽检。

第一阶段建议：

- 为摘要、审核、伏笔和角色判断分别定义 judge rubric。
- judge prompt 固定版本，记录 judge model、prompt_version、输入输出和分数。
- 输出结构化分数：
  - consistency_score
  - character_score
  - foreshadowing_score
  - style_score
  - blocking_findings
- 保留少量人工校准样例，避免 judge 漂移。

验收方式：

- 前端 Eval 面板能看到 LLM judge 评分和理由。
- 同一批样例在同一 judge prompt/model 下可重复回放。

涉及模块：

- `docs/modules/evaluation.md`
- `docs/modules/model-provider.md`

### 混合检索与 reranker

状态：

- 当前 RAG 以向量检索为主。
- 还没有关键词检索、混合召回、重排模型和多路召回融合。

目标：

- 提升 RAG 对专有名词、伏笔名、章节标题、角色名的召回稳定性。
- 通过 reranker 提高 top k 排序质量，减少无关内容进入上下文预算。

第一阶段建议：

- 增加轻量关键词召回：按角色名、伏笔关键词、章节标题、状态字段匹配。
- 与向量召回做 union，去重后保留来源和分数。
- 暂不接重模型 reranker 时，可先做规则式 rerank：
  - RAG 相似度。
  - 关键词命中。
  - 未回收伏笔优先。
  - 当前角色优先。
  - 最近章节优先。
- 后续再接本地或外部 reranker。

验收方式：

- RAG Eval 指标可比较“纯向量”和“混合检索”的差异。
- 后台能看到每条召回结果来源：vector、keyword、hybrid、reranked。

涉及模块：

- `docs/modules/retrieval.md`
- `docs/modules/evaluation.md`

### tokenizer 级上下文预算

状态：

- 当前上下文预算使用字符数或粗略 token 估算。
- Agent 后台能看到预算占用，但这不是 provider 真实 tokenizer 结果。

目标：

- 将上下文预算从字符估算升级为 tokenizer 级或 provider usage 级估算。
- 更准确地区分“模型上下文窗口”“最大输出 token”“系统主动上下文预算”。

第一阶段建议：

- 在 `model_provider` 或独立 `token_counter` 层提供统一 token 估算接口。
- 无 tokenizer 时保留字符估算 fallback。
- `load_context.context_budget` 同时记录：
  - estimated_tokens
  - estimated_chars
  - model_max_tokens
  - reserved_output_tokens
  - context_budget_tokens
- 前端显示“上下文预算占用”时明确这是估算值。

验收方式：

- 生成任务能看到本次上下文估算 token。
- 调整模型最大输出 token 时，上下文预算预留空间随之变化。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/model-provider.md`

### 用户反馈数据闭环

状态：

- 当前已有采纳/拒绝生成记录，训练数据导出默认只导出已采纳记录。
- 还没有系统化记录用户对正文、摘要、审核发现、伏笔建议、角色卡建议的细粒度反馈。

目标：

- 记录用户对生成正文、摘要、审核发现、伏笔建议、角色卡建议的采纳、拒绝和修改。
- 将反馈沉淀为后续 eval、prompt 优化、检索优化或微调数据。
- 区分用户审美修改、事实纠错、结构问题和随意改写，避免把所有修改都当成模型错误。

第一阶段建议：

- 新增反馈记录模型，至少包含：
  - target_type：chapter / summary / audit / foreshadowing / character_period
  - action：accepted / rejected / edited
  - reason_type：style / factual_error / consistency / pacing / other
  - before / after 摘要或 diff
  - related_task_id / chapter_id
- 先记录，不自动训练、不自动改 prompt。

验收方式：

- 用户采纳、拒绝或修改候选结果时，能保存反馈记录。
- 训练数据导出可以选择性包含高质量反馈样本。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/training-data.md`
- 后续可新增 `docs/modules/feedback-loop.md`

### LLM 平滑切换

状态：

- 已完成基础能力：全局运行时模型配置 API、前端模型工具条、任务级模型配置快照、生成记录模型快照、重试使用任务快照、API key 不返回也不写入快照。
- 后续细化：持久化非敏感配置、多进程同步、项目级模型配置、更多 provider。

目标：

- 支持运行时切换默认 LLM。
- 新生成任务使用切换后的模型。
- 已开始任务继续使用任务创建时的模型配置，避免生成结果不可复现。
- 生成记录保存实际 provider、base_url、model 和关键参数摘要。

第一阶段建议只做全局切换，不做项目级或节点级模型配置。

涉及模块：

- `docs/modules/model-provider.md`
- `docs/modules/generation-flow.md`

### AI 生成期间输入锁定

状态：

- 已完成基础能力：生成/全自动/保存/采纳/拒绝/重试期间复用前端 `busy` 状态锁定正文、小说想法、作者灵感、模型配置和生成控制；后台继续显示任务状态和节点进度。

目标：

- 用户只能在 AI 生成前或生成后输入。
- 生成、审核、保存、重试期间锁定正文、灵感和关键设定输入。
- 锁定期间展示任务状态和节点进度。

涉及模块：

- `docs/modules/generation-flow.md`

### AI 评判用户输入是否合理

状态：

- 已完成基础能力：项目想法和作者灵感写入前调用 AI 评判；结果包含通过、警告、阻止、原因和建议；阻止结果不会创建项目或写入灵感；前端展示最近一次评判结果。
- 当前边界：暂不接入已采纳章节正文修改，因为第一版不开放完整的已采纳章节重写/修改流程。
- 后续细化：warning 二次确认、评判历史入库、正文修改影响评估。

目标：

- 用户提交小说想法、作者灵感、正文改动或关键设定改动后，AI 可以先评判输入是否合理。
- 评判结果至少包含：通过、警告、阻止。
- 第一阶段只给出原因和修改建议，不自动改写用户输入。

判断维度：

- 是否和世界观冲突。
- 是否破坏角色动机。
- 是否和前文摘要矛盾。
- 是否提前泄露伏笔。
- 是否偏离项目定位或章节目标。
- 是否过于模糊，无法指导后续生成。

涉及模块：

- `docs/modules/generation-flow.md`
- 后续可新增 `docs/modules/author-interaction.md`

### SSE 流式输出

状态：

- 已完成基础能力：单章生成和指定章数全自动生成均使用 SSE；前端按 11 个中文 LangGraph 节点实时更新后台进度，并在 `generate_prose` 完成后直接把候选正文写入中部正文区。
- 后续细化：token 级逐字正文流、断线后自动重连和独立任务事件订阅接口。

目标：

- 章节生成过程通过 SSE 向前端推送节点状态、模型输出进度、审核结果和失败信息。
- 前端不需要轮询生成任务即可看到后台生成进度。
- 断线后前端可以重新拉取任务详情，继续展示已落库的任务步骤。

第一阶段建议：

- 后端新增任务事件流接口，例如 `GET /api/generation-tasks/{task_id}/events`。
- SSE 事件至少包含：`task_started`、`step_started`、`step_completed`、`step_failed`、`task_completed`、`task_failed`。
- 真实 token 级流式文本可以后续再做；第一阶段先流式推送节点级进度和关键输出摘要。

涉及模块：

- `docs/modules/generation-flow.md`

### 上下文预算管理

状态：

- 已完成基础能力：`load_context` 使用规则式字符预算裁剪章节摘要、事件、灵感、伏笔和世界观规则，并在 Agent 后台上下文视图展示预算占用和被裁剪内容摘要。
- 后续细化：模型 tokenizer 估算、固定上下文预算统计和更细的优先级策略。

目标：

- 为 `load_context` 增加明确的上下文预算，避免章节增多后把所有摘要、角色、伏笔和灵感无差别塞入 prompt。
- 按优先级分配 token 或字符预算：核心设定固定加载，当前章节目标固定加载，当前角色和未回收伏笔优先加载，最近章节摘要优先加载，旧信息按相关性加载。
- 在后台展示本次上下文包的组成、预算占用和被裁剪内容摘要，方便调试幻觉来源。

第一阶段建议：

- 先做规则式预算，不做向量检索。
- 预算单位可以先用字符数或粗略 token 估算，后续再接模型 tokenizer。

涉及模块：

- `docs/modules/generation-flow.md`

### 结构化记忆：角色时期卡、事件时间线和世界观规则表

状态：

- 已完成基础能力：角色时期字段和展示、事件时间线、世界观规则表、`load_context` 加载、采纳后写入正式结构化记忆。
- 后续细化：更多实体类型、逐条人工确认、检索字段和质量评测。

目标：

- 把长期稳定事实从章节摘要中拆出来，减少摘要越来越长、越来越漂移的问题。
- 角色卡必须支持当前时期/阶段显示，至少包含阶段名、当前目标、关键记忆、关系变化和阶段变化来源章节。
- 新增事件时间线，记录关键事件、章节、涉及角色、地点和后果。
- 新增世界观规则表，记录规则、限制、例外、来源章节和当前有效状态。
- 生成后由 AI 提取候选事实，审核通过或用户确认后进入正式记忆。
- 右侧模块栏和 Agent 后台上下文视图都要能看到角色当前时期，避免 `judge_character_period` 只在后台节点里有判断结果、正式角色卡却没有稳定状态。

第一阶段建议：

- 先补角色时期卡字段和展示，再支持事件时间线和世界观规则。
- 不一次性扩展到地点、物品、阵营等所有实体。

涉及模块：

- `docs/modules/generation-flow.md`
- 后续可新增 `docs/modules/memory-system.md`

### RAG 检索：按角色、伏笔、地点召回旧信息

状态：

- 已完成基础能力：Docker Qdrant 向量库、本地免费 embedding、测试用 hash embedding、正式记忆向量召回、`load_context` 接入、上下文预算接入、Agent 后台召回展示。
- 后续细化：索引重建 API、混合检索、重排、embedding 批处理、recall@k 评估和更多实体类型。

目标：

- 当前章节生成前，根据章节目标、涉及角色、伏笔、地点和关键词召回相关旧信息。
- 检索来源包括章节摘要、事件时间线、世界观规则、角色卡、伏笔表。
- 检索结果进入上下文预算管理，由预算器决定哪些内容进入最终 prompt。

第一阶段实现：

- 使用 Qdrant 作为 Docker 向量数据库。
- 使用 `BAAI/bge-small-zh-v1.5` 作为 Docker 运行时本地 embedding 模型。
- 本地测试默认使用确定性 hash embedding，避免测试依赖模型下载。
- 向量召回结果进入上下文预算管理，最终仍由预算器控制 prompt 内容。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/retrieval.md`

### Eval：摘要事实保留率和审核冲突检出率

状态：

- 已完成基础能力：确定性 eval 函数、摘要事实保留率、审核冲突检出率、内置 gold case、命令行回放 runner。
- 后续细化：接入真实 `GenerationRun`、入库保存 eval 结果、precision/recall/F1、前端报告历史趋势。

目标：

- 建立模型质量评测，不只依赖人工感觉判断“生成好不好”。
- 摘要节点评估事实保留率：章节中关键事实是否被摘要保留。
- 审核节点评估冲突检出率：已知世界观、人设、前文冲突是否能被识别。
- 评测样例和结果可以回放，用于比较 prompt、模型和检索策略变化。

第一阶段建议：

- 先维护少量人工 gold case，覆盖摘要、审核、伏笔泄露、人设冲突。
- 指标先用通过率和漏检记录，后续再扩展 precision、recall、F1。

涉及模块：

- `docs/modules/generation-flow.md`
- `docs/modules/evaluation.md`

### 模型路由：生成、摘要、审核可选不同模型

状态：

- 已完成基础能力：支持 `generation`、`audit`、`summary` 三类路由；新任务快照保存默认模型和路由配置；重试复用任务快照；三类节点输出实际使用的模型配置；前端工具条可配置三类路由模型名。
- 后续细化：每条路由独立 provider/base URL/max tokens UI、项目级路由配置、更多节点路由。

目标：

- 支持按节点选择模型，例如正文生成用强模型，摘要用低成本模型，审核用稳定模型。
- 每个任务必须保存节点实际使用的 provider、base_url、model 和关键参数，保证生成记录可复现。
- 已开始任务继续使用创建时的模型配置快照。

第一阶段建议：

- 必须先完成或复用 LLM 平滑切换和任务级模型配置快照。
- 初期只开放生成、摘要、审核三类节点路由，不把所有节点都做成可配置。

涉及模块：

- `docs/modules/model-provider.md`
- `docs/modules/generation-flow.md`

### 成本和 token 统计

状态：

- 已完成基础能力：章节生成六个模型调用节点记录估算输入/输出 token、耗时、route、公开模型配置和估算成本；采纳/拒绝生成记录保存聚合 usage；Agent 后台展示当前任务估算 token、成本和耗时。
- 后续细化：真实 provider usage 解析、按模型/路由分别配置价格、项目级成本报表。

目标：

- 记录每次模型调用的输入 token、输出 token、耗时、模型和估算成本。
- 在生成记录和 Agent 后台展示本章、本次全自动任务的累计消耗。
- 为上下文预算、模型路由和成本优化提供数据依据。

第一阶段建议：

- 如果 provider 不返回 token usage，先记录估算值和实际耗时。
- 成本单价先配置化，不写死在业务逻辑里。

涉及模块：

- `docs/modules/model-provider.md`
- `docs/modules/generation-flow.md`

### 微调准备

状态：

- 已完成基础能力：从已采纳 `GenerationRun` 导出 provider-neutral JSONL 样本，覆盖上下文到正文、正文到摘要、正文到审核结果；默认排除拒绝记录；导出清理 `api_key` 相关字段；提供 CLI 入口。
- 当前边界：不训练、不上传、不做 provider 专有格式转换；用户修改前后对比等待完整正文修改流程后再采集。

目标：

- 不在第一阶段直接做微调，但开始为未来微调准备干净数据。
- 收集稳定样本：上下文包到章节正文、正文到摘要、正文到审核结果、用户修改前后对比。
- 明确微调适用边界：优先用于固定格式输出、摘要风格、审核标准或文风一致性；不把上下文缺失问题交给微调解决。

第一阶段建议：

- 先完成 eval 和用户反馈数据闭环，再判断是否需要微调。
- 需求池中保留为 P0，是因为数据采集边界需要尽早设计；真正训练可以后置。

涉及模块：

- `docs/modules/model-provider.md`
- `docs/modules/generation-flow.md`
- 后续可新增 `docs/modules/training-data.md`

## P1

### 创作后台布局优化

目标：

- 底部 Agent 创作后台支持展开和收起。
- 创作后台始终位于主内容下方，并处在左侧章节栏和右侧模块栏之间，不覆盖左右栏。
- 页面整体不应依赖浏览器整页滚动。
- 中间正文区、右侧模块栏、底部 Agent 创作后台各自负责内部滚动。
- 右侧模块栏必须是独立滑动栏，不能拖动整个页面。

降级原因：

- 当前基础布局和后台展示已经可用于第一版验收。
- 后续主要是体验打磨，不应阻塞上下文、记忆、检索和评测能力。

涉及模块：

- 后续可新增轻量 `docs/modules/editor-workspace.md`

### 项目级模型配置

不同小说项目可以绑定不同默认模型。适合在全局 LLM 切换稳定后实现。

### 更细的记忆确认流程

角色卡、伏笔、摘要更新建议由用户逐条确认后再进入正式上下文。

## P2

### 节点级恢复与单节点重试

状态：

- 当前已有任务状态、节点快照、失败记录和重试入口。
- 重试时可以复用已完成节点的 `output_snapshot`，但还不是完整产品化的“从失败节点继续”和“单节点重试”。

降级原因：

- 当前整任务重试已经能支撑第一版闭环和基础失败恢复。
- 单节点重试会涉及下游节点失效、回滚边界、尝试次数和用户操作入口，复杂度较高，当前不重要，降为 P2。

目标：

- 失败后可以基于已完成节点快照继续执行，避免整章从头重跑。
- 支持针对单个失败节点重试，并保留失败原因、重试次数和每次尝试的快照。
- 区分关键节点和非关键节点：正文生成、审核、候选保存失败应阻塞；部分判断节点失败可降级但必须记录。

第一阶段建议：

- `GenerationTaskStep` 增加或派生：
  - `attempt_count`
  - `retryable`
  - `last_error_type`
  - `last_error_message`
- 新增单节点重试 API，例如：
  - `POST /api/generation-tasks/{task_id}/steps/{step_name}/retry`
- 前端失败节点显示“重试此节点”。
- 明确哪些节点允许复用快照，哪些节点上下文变化后必须重算。

验收方式：

- 人为让某个节点失败后，前端能看到失败节点。
- 点击单节点重试后，只重新执行失败节点及其后续依赖节点。
- 已完成且允许复用的节点不会重复调用模型。

涉及模块：

- `docs/modules/generation-flow.md`

### 桌面端打包

使用 Tauri 打包桌面端。

### 富文本编辑器

支持更好的章节编辑体验，但不影响第一版闭环。

## 使用规则

- 新想法先加入本需求池，不直接进入开发。
- 每次只选择一个 P0/P1 小需求进入设计。
- 设计和实施计划由 AI 使用 superpowers 流程处理，不作为用户需要维护的产品文档。
- 如果需求涉及已有模块，写计划前必须阅读 `docs/modules/` 中对应模块文档。
