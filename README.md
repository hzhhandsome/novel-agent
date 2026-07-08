# Novel Agent

第一版目标：跑通“输入小说想法 -> Agent 生成设定和章节规划 -> 生成单章 -> 作者采纳或补充灵感 -> 后续继续生成”的自动化小说生成闭环。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + SQLAlchemy + Alembic
- Agent 编排：LangGraph
- 中间件：PostgreSQL
- 默认运行环境：Docker Compose

## Docker 启动

```powershell
docker compose up --build
```

服务地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- PostgreSQL：`localhost:55432`

后端容器启动时会先执行 `alembic upgrade head`，再启动 FastAPI。

## Docker 验证

后端测试：

```powershell
docker compose run --rm backend python -m pytest -v
```

前端测试和构建：

```powershell
docker compose run --rm frontend npm test -- --run
docker compose run --rm frontend npm run build
```

## 本地启动备选

后端：

```powershell
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

默认配置见 `.env.example`。

## 本地验证备选

后端：

```powershell
cd backend
python -m pytest -v
```

前端：

```powershell
cd frontend
npm test -- --run
npm run build
```

## 当前第一版能力

- 创建小说项目并生成基础设定、世界观、主线、角色卡和前三章规划。
- 通过 LangGraph 生成项目初始化结果。
- 通过 LangGraph 节点化生成单章候选正文。
- 落库记录生成任务和每个节点步骤状态。
- 模拟节点失败后，可从已保存任务重试。
- 作者可采纳或拒绝候选章节。
- 作者可追加灵感，后续生成会读取未应用灵感。
- 前端提供四区工作台：章节、正文、模块、Agent 创作后台。
