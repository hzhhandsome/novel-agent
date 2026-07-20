# 评测模块

## 模块职责

评测模块负责用稳定样例衡量生成流程质量，避免只靠人工感觉判断摘要和审核是否可靠。

当前第一阶段覆盖四个 P0 指标：

- 摘要事实保留率：摘要是否保留预期关键事实。
- 审核冲突检出率：审核发现是否命中预期冲突。
- RAG 召回质量：关键旧信息是否出现在 top k，且排序是否靠前。
- LLM-as-judge 语义评测：用固定 rubric 评估一致性、人设、伏笔和文风。

## 入口文件

- `backend/app/services/evaluation.py`：纯评测函数。
- `backend/app/evals/gold_cases.py`：内置 gold case。
- `backend/app/evals/rag_cases.py`：内置 RAG retrieval gold case。
- `backend/app/evals/judge_cases.py`：内置 LLM judge gold case。
- `backend/app/evals/run.py`：命令行回放入口。
- `backend/tests/test_evaluation.py`：评测行为测试。

## 核心流程

1. 在 gold case 中定义预期事实、预期冲突或预期召回文档。
2. 用模型输出、候选摘要或审核发现作为被评测文本。
3. 摘要和审核评测函数按 label 和 alias 做确定性文本匹配。
4. 输出每个 case 的命中项、遗漏项、通过阈值和指标分数。
5. RAG Eval 使用固定 retrieval report 和 expected source id 计算 `recall@k`、`precision@k`、`hit_rate@k` 和 `MRR`。
6. LLM-as-judge Eval 读取固定 judge case，通过当前 `ModelProvider.judge_eval_case()` 按 rubric 返回结构化语义分。
7. runner 汇总平均事实保留率、平均冲突检出率、RAG 召回指标、judge 平均分和通过数量。

运行方式：

```powershell
cd backend
python -m app.evals.run
```

## 数据和状态

当前不新增数据库表。评测样例以代码形式维护，便于在 CI 或本地快速回放。

结果字段：

- `summary.average_retention_rate`
- `audit.average_recall_rate`
- `rag.average_recall_at_k`
- `rag.average_precision_at_k`
- `rag.average_hit_rate_at_k`
- `rag.average_mrr`
- `judge.average_score`
- `judge.passed_count`
- `overall.case_count`
- `overall.passed_count`
- `prompt_versions.case_count`
- `prompt_versions.groups[].prompt_version`
- `prompt_versions.groups[].case_count`
- `prompt_versions.groups[].passed_count`
- 每个 case 的 `retained` / `missing`、`detected` / `missed`、`blocking_findings`、`reason`

RAG Eval 第一阶段只使用内置固定 retrieval report，不读取真实项目数据库，也不直接调用 Qdrant。这样指标稳定、可重复，适合比较后续 query 构造、chunk 策略、混合检索和 reranker 改动。

LLM-as-judge 第一阶段只作为离线 Eval 工具，不插入章节生成 11 节点流程，也不把 judge 结果写入数据库。它使用少量固定 case 和固定 rubric，输出 `consistency`、`character`、`foreshadowing`、`style` 四类 0-1 分数、平均分、阻塞发现和理由。

## 扩展点

后续可以增加：

- 读取真实 `GenerationRun` 作为被评测输出。
- 把 eval 结果入库，用于比较 prompt、模型、RAG 策略。
- 摘要和审核的 precision、recall、F1 和 false positive 记录。
- embedding 语义匹配。
- 读取真实 `GenerationRun` 和真实检索日志，计算在线 RAG Eval。
- 前端评测报告页和历史趋势。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_evaluation.py -v
```

完整后端验证：

```powershell
cd backend
python -m pytest -v
python -m app.evals.run
```

## 后续修改注意事项

- gold case 要保持小而稳定，避免为了让当前模型“好看”而频繁改答案。
- 新增模型、prompt 或 RAG 策略后，应优先复用同一批 gold case 做对比。
- LLM judge 是辅助语义评测，不能替代确定性 gold case 和人工抽检。
- 修改内置 Eval prompt 或评测规则时，必须同步更新 `builtin_eval` prompt version，避免不同规则下的结果混在同一版本里。
- 修改 judge rubric 时，必须同步更新 `llm_judge_eval` prompt version。

## 前端/API 入口

前端可通过 Agent 创作后台的“运行 Eval”按钮触发内置评测。

后端 API：

```http
GET /api/evals/builtin
```

该接口复用 `backend/app/evals/run.py` 的 `run_builtin_evals()`，返回结构与命令行 `python -m app.evals.run` 保持一致。当前接口只读取内置 gold cases，不写数据库。RAG 部分读取内置固定 retrieval report，不依赖实时向量库状态。

## 2026-07-19 更新

- 前端 Eval 报告继续显示在 Agent 后台“结果与更新”tab。
- 当前 Eval 仍以确定性 gold case 为主，用于摘要事实保留率、审核冲突检出率和固定 RAG 召回质量；不能宣称已经覆盖完整语义评测。
- RAG 召回质量已作为独立指标输出，不混入摘要和审核 Eval 指标。

## 2026-07-20 更新

- 新增内置 RAG Eval，输出 `recall@k`、`precision@k`、`hit_rate@k` 和 `MRR`。
- `python -m app.evals.run` 和 `GET /api/evals/builtin` 均返回 `rag` 聚合结果。
- 前端 Agent 后台“运行 Eval”后会展示 RAG 召回率和 RAG MRR。
- 当前 RAG Eval 使用固定 retrieval report，后续再接真实检索日志和策略对比。
- 新增 `prompt_versions` 聚合，内置 Eval 结果会按 `builtin_eval@2026-07-20.v1` 分组，后续可用于比较不同 prompt/rubric 版本。
- 新增轻量 LLM-as-judge Eval，`python -m app.evals.run` 和 `GET /api/evals/builtin` 均返回 `judge` 聚合结果。
- 前端 Agent 后台 Eval 卡展示 Judge 语义分、通过数量和阻塞发现。
