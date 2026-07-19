# Eval 前端展示与顶部工具栏折叠设计

## 背景

当前 Eval 只能通过命令行运行：

```powershell
cd backend
python -m app.evals.run
```

这不方便在前端验证“摘要事实保留率”和“审核冲突检出率”。同时顶部生成工具栏包含模型配置、全自动生成等控制，常驻展开会占用正文空间。

已阅读模块文档：

- `docs/modules/evaluation.md`

## 设计

1. 后端新增一个只读 API：`GET /api/evals/builtin`，直接复用 `run_builtin_evals()` 的结果结构，不新增数据库表，不改变现有 CLI。
2. 前端新增 Eval 类型和客户端函数，在 Agent 创作后台中增加“运行 Eval”按钮，点击后展示整体通过数、摘要事实保留率、审核冲突检出率和失败样例。
3. 顶部生成工具栏增加展开/收起状态。默认展开；收起时保留“全自动状态”和展开按钮，隐藏模型配置、章数和生成按钮。
4. 生成期间正文仍然禁用编辑；工具栏折叠按钮不参与生成流程，不改变 LangGraph 11 节点。
5. 向量数据库不新增容器，因为 `docker-compose.yml` 已包含 `qdrant`，Postgres 镜像也已使用 `pgvector/pgvector:pg16`。

## 测试

- 后端测试覆盖 `GET /api/evals/builtin` 的响应结构。
- 前端测试覆盖点击“运行 Eval”后报告显示。
- 前端测试覆盖顶部工具栏收起后隐藏模型配置、再次展开后恢复。
