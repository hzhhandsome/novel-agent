# 训练数据准备模块

## 模块职责

训练数据准备模块负责把已经验收的生成记录导出为干净、可回放、厂商无关的 JSONL 样本，为未来微调或离线评测做准备。本模块不负责训练模型、不上传数据、不绑定任何 provider 的专有格式。

## 入口文件

- `backend/app/services/training_data.py`：从 `GenerationRun` 转换训练样本，并写出 JSONL。
- `backend/app/training_data/export.py`：命令行导出入口。
- `backend/tests/test_training_data.py`：导出服务和 CLI wrapper 测试。

## 核心流程

1. 查询 `GenerationRun`。
2. 默认只选择 `accepted=True` 的记录。
3. 按一条生成记录拆出多类样本：
   - `context_to_chapter`：上下文提示包 -> 已采纳章节正文。
   - `chapter_to_summary`：已采纳章节正文 -> 章节摘要。
   - `chapter_to_audit`：提示包和章节正文 -> 审核结果。
4. 写出 JSONL，每行一个 JSON object。

命令示例：

```powershell
python -m app.training_data.export exports/training.jsonl
```

如需包含拒绝记录：

```powershell
python -m app.training_data.export exports/training.jsonl --include-rejected
```

## 数据和状态

每条样本包含：

- `task_type`：样本任务类型。
- `input`：模型输入。
- `output`：期望输出。
- `metadata`：项目、章节、任务、生成记录、模型快照和 usage 快照。

导出时会清理包含 `api_key` 的字段，避免训练样本出现密钥相关字段。

## 当前边界

- 不做实际微调。
- 不做 provider-specific 格式转换。
- 不导出用户修改前后对比，因为第一版暂不开放完整正文修改流程。
- 不保证样本足够训练，只保证数据边界和格式先稳定。

## 测试方式

```powershell
python -m pytest backend/tests/test_training_data.py -v
```

## 后续修改注意事项

- 新增训练样本类型时，必须明确输入、输出和采纳边界。
- 不要把未采纳候选默认混入训练集；需要时必须显式使用 `include_rejected`。
- 如果接入用户反馈数据，应区分事实纠错、风格偏好和用户随意改写。
