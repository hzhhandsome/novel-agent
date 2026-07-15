# 模型提供器模块

## 模块职责

模型提供器模块负责把业务流程和具体 LLM 厂商隔离开。业务代码只依赖 `ModelProvider` 协议，不直接绑定 DeepSeek、OpenAI 或其他模型 API。

## 入口文件

- `backend/app/services/model_provider.py`：`ModelProvider` 协议、Mock provider、DeepSeek Anthropic-compatible provider。
- `backend/app/services/provider_factory.py`：根据配置创建当前 provider。
- `backend/app/core/config.py`：模型相关环境变量配置。
- `.env.example`：模型配置示例，不包含真实密钥。

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

返回值必须是结构化 dataclass，业务层不直接解析模型原始响应。

## 扩展点

后续可添加：

- 运行时全局模型切换。
- 项目级模型配置。
- 节点级模型配置。
- 模型调用成本、耗时和失败原因记录。
- 温度、最大 token、超时和重试策略。

LLM 平滑切换第一阶段建议做全局切换：新任务使用新模型，已开始任务继续使用创建任务时记录的模型配置。

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
