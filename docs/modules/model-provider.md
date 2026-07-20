# 模型提供器模块

## 模块职责

模型提供器模块负责把业务流程和具体 LLM 厂商隔离开。业务代码只依赖 `ModelProvider` 协议，不直接绑定 DeepSeek、OpenAI 或其他模型 API。

## 入口文件

- `backend/app/services/model_provider.py`：`ModelProvider` 协议、Mock provider、DeepSeek Anthropic-compatible provider。
- `backend/app/services/provider_factory.py`：维护运行时模型配置，根据当前配置或任务快照创建 provider。
- `backend/app/core/config.py`：模型相关环境变量配置。
- `.env.example`：模型配置示例，不包含真实密钥。
- `backend/app/api/routes/generation.py`：`GET/PUT /api/model-config` 运行时模型切换 API。

## 当前 Provider

### MockModelProvider

用于测试和本地无模型环境。

特点：

- 不调用外部 API。
- 返回结构化项目设定、章节正文、审核结果和摘要。
- 后端测试默认强制使用 mock，避免本机 `.env` 的真实模型配置污染测试。

### DeepSeekAnthropicProvider

使用 DeepSeek Anthropic-compatible API。

当前配置项：

- `NOVEL_AGENT_MODEL_PROVIDER=deepseek`
- `NOVEL_AGENT_MODEL_BASE_URL=https://api.deepseek.com/anthropic`
- `NOVEL_AGENT_MODEL_NAME=deepseek-v4-flash`
- `NOVEL_AGENT_MODEL_API_KEY=<local secret>`
- `NOVEL_AGENT_MODEL_MAX_TOKENS=4096`

密钥只能进入本机 `.env` 或部署密钥系统，不能提交到仓库。

## 核心接口

`ModelProvider` 当前包含：

- `generate_project_setup(idea)`
- `generate_chapter(prompt_package)`
- `review_chapter(content, prompt_package)`
- `summarize_chapter(content)`
- `judge_foreshadowing(content, context, existing_items)`
- `judge_character_period(content, context, characters)`
- `propose_future_plan_updates(content, context, chapters)`
- `review_user_input(input_kind, content, context)`
- `judge_eval_case(input_text, context, rubric)`

返回值必须是结构化 dataclass，业务层不直接解析模型原始响应。

`judge_eval_case` 只用于离线 Eval，不进入章节生成 11 节点流程。它返回 `JudgeEvalResult`，包含 `scores`、`blocking_findings` 和 `reason`，由 Eval 模块再计算平均分和通过状态。

## LLM 平滑切换

当前支持第一阶段全局运行时切换：

- `GET /api/model-config` 返回当前 provider、base URL、model、max tokens 和 `api_key_set`。
- `PUT /api/model-config` 更新当前后端进程内的全局模型配置。
- API key 只进入运行时内存，不返回给前端，也不写入任务快照或生成记录。
- 新建生成任务时，`GenerationTask.model_config_snapshot` 保存 provider、base URL、model、max tokens 和 `api_key_set`。
- 重试任务时优先使用该任务已有的 `model_config_snapshot`，不受后续全局模型切换影响。
- `GenerationRun.model_config_snapshot` 保存采纳或拒绝时对应任务的模型配置快照，便于回看。

当前切换配置是进程内状态，重启后回到环境变量配置。项目级模型配置和节点级模型路由属于后续需求。

## 模型路由

当前支持第一阶段节点级路由：

- `generation`：用于 `generate_prose` 正文生成节点。
- `audit`：用于 `audit_prose` 审核节点。
- `summary`：用于 `summarize_chapter` 摘要节点。

`GET /api/model-config` 会返回 `routes`。`PUT /api/model-config` 可以写入或清除三类路由；路由未配置时继承任务默认模型配置。前端第一阶段只开放三类路由的模型名字段，provider、base URL 和 max tokens 继承当前默认配置，避免工具条过度复杂。

新建任务时，`GenerationTask.model_config_snapshot` 会同时保存默认配置和路由配置。重试任务时继续使用任务快照中的路由，不读取后续全局切换结果。三类路由节点会在 `GenerationTaskStep.output_snapshot` 中保存本节点实际使用的公开模型配置，例如 `generation_model_config`、`audit_model_config` 和 `summary_model_config`。

API key 仍只保存在运行时内存中，不返回前端，也不写入默认或路由快照。

## 成本和 token 统计

当前第一阶段记录章节生成流程中的模型调用估算数据：

- 覆盖节点：`generate_prose`、`audit_prose`、`summarize_chapter`、`judge_foreshadowing`、`judge_character_period`、`propose_future_plan_updates`。
- 每个节点输出快照包含 `<node>_model_usage`，记录 route、公开模型配置、估算输入 token、估算输出 token、耗时毫秒和估算成本。
- `GenerationRun.model_usage_snapshot` 在采纳或拒绝候选时保存本次任务聚合 usage。
- 前端 Agent 后台展示当前任务估算 token、估算成本和耗时。

同一批模型调用节点也会记录 prompt 版本元数据：

- `<node>_prompt_metadata`：记录该节点实际输入对应的 prompt template、prompt version、prompt hash 和 context builder version。
- `GenerationRun.model_usage_snapshot.prompt_versions`：聚合一次生成任务中各节点 prompt 版本。

第一阶段 prompt 版本信息保存在现有 JSON 快照中，不新增独立 prompt 表，也不改变 provider 接口。

估算 token 当前使用确定性字符启发式，不依赖外部 tokenizer。成本单价通过环境变量配置，默认 0：

- `NOVEL_AGENT_MODEL_INPUT_COST_PER_1K`
- `NOVEL_AGENT_MODEL_OUTPUT_COST_PER_1K`

后续如果 provider 返回真实 usage，应在 provider/usage 层替换估算值，不改变业务层字段形状。

## 扩展点

后续可添加：

- 运行时全局模型切换。
- 项目级模型配置。
- 节点级模型配置已经覆盖正文生成、审核和摘要三类 P0 路由；更多节点路由可后续扩展。
- 模型调用成本和耗时已经支持第一阶段估算记录；真实 provider usage 和更细价格表可后续扩展。
- 温度、最大 token、超时和重试策略。
- 独立 prompt 模板管理、版本 diff 和按 prompt version 的历史质量报表。

LLM 平滑切换第一阶段已经支持全局切换：新任务使用新模型，已开始任务继续使用创建任务时记录的模型配置快照。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_model_provider.py backend/tests/test_provider_factory.py -v
```

密钥扫描：

```powershell
rg -n "sk-[A-Za-z0-9]" .env.example backend/app backend/tests
```

## 后续修改注意事项

- 不要在业务服务里直接调用某个厂商 SDK 或 HTTP API。
- 新增 provider 时必须补 provider factory 测试。
- 新增模型配置时必须更新 `.env.example`，但不能写真实密钥。
- 如果模型响应结构改变，优先在 provider 层解析和校验，不把不稳定格式泄漏到 LangGraph 节点。
- 不要把 API key 明文写入 `GenerationTask.model_config_snapshot` 或 `GenerationRun.model_config_snapshot`。
- 修改模型调用节点 prompt 输入时，必须同步更新 `backend/app/services/prompt_versions.py` 中的版本号和对应测试。
- 修改 LLM-as-judge rubric 或输出结构时，必须同步更新 `llm_judge_eval` prompt version 和 provider 解析测试。

## 2026-07-19 更新

- “模型最大 token”表示一次模型调用中输入和输出共享的窗口上限。
- “上下文预算”是系统主动分配给长期记忆、摘要、伏笔、灵感等上下文的预算，应小于模型最大 token，并为系统提示、本章目标和正文输出预留空间。
- Agent 后台顶部显示的上下文占用来自 `load_context.context_budget`，用于观察上下文是否接近预算上限；当前仍是粗略估算，不等同于 provider 返回的真实 tokenizer 计数。

## 2026-07-20 更新

- 模型调用节点新增 `<node>_prompt_metadata`，用于回看本次调用使用的 prompt version、hash 和 context builder version。
- 采纳/拒绝生成记录会在 `model_usage_snapshot.prompt_versions` 中保存各节点 prompt 版本聚合。
- 新增 `judge_eval_case` provider 方法，供内置 Eval 执行轻量 LLM-as-judge 语义评测。
