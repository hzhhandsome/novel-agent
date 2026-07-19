# 评测模块

## 模块职责

评测模块负责用稳定样例衡量生成流程质量，避免只靠人工感觉判断摘要和审核是否可靠。

当前第一阶段覆盖两个 P0 指标：

- 摘要事实保留率：摘要是否保留预期关键事实。
- 审核冲突检出率：审核发现是否命中预期冲突。

## 入口文件

- `backend/app/services/evaluation.py`：纯评测函数。
- `backend/app/evals/gold_cases.py`：内置 gold case。
- `backend/app/evals/run.py`：命令行回放入口。
- `backend/tests/test_evaluation.py`：评测行为测试。

## 核心流程

1. 在 gold case 中定义预期事实或预期冲突。
2. 用模型输出、候选摘要或审核发现作为被评测文本。
3. 评测函数按 label 和 alias 做确定性文本匹配。
4. 输出每个 case 的命中项、遗漏项、通过阈值和指标分数。
5. runner 汇总平均事实保留率、平均冲突检出率和通过数量。

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
- `overall.case_count`
- `overall.passed_count`
- 每个 case 的 `retained` / `missing` 或 `detected` / `missed`

## 扩展点

后续可以增加：

- 读取真实 `GenerationRun` 作为被评测输出。
- 把 eval 结果入库，用于比较 prompt、模型、RAG 策略。
- precision、recall、F1 和 false positive 记录。
- LLM-as-judge 或 embedding 语义匹配。
- 前端评测报告页。

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
- 当前是确定性文本匹配，不能声称已经有完整语义评测；语义匹配和 LLM judge 应作为后续增强。

## 前端/API 入口

前端可通过 Agent 创作后台的“运行 Eval”按钮触发内置评测。

后端 API：

```http
GET /api/evals/builtin
```

该接口复用 `backend/app/evals/run.py` 的 `run_builtin_evals()`，返回结构与命令行 `python -m app.evals.run` 保持一致。当前接口只读取内置 gold cases，不写数据库。

## 2026-07-19 更新

- 前端 Eval 报告继续显示在 Agent 后台“结果与更新”tab。
- 当前 Eval 仍是确定性 gold case 文本匹配，用于摘要事实保留率和审核冲突检出率；不能宣称已经覆盖完整语义评测。
- 后续如果要衡量 RAG 召回质量，应新增 recall@k / MRR 类指标，不要混入当前摘要和审核 Eval 指标。
