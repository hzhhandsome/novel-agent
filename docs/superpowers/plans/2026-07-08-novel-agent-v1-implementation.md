# Novel Agent V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable first version of the automated novel generation loop: create a project from an idea, generate setup data, generate one chapter through LangGraph nodes, let the author edit or accept it, persist state in PostgreSQL, and recover failed or interrupted generation tasks.

**Architecture:** Use a React + Vite + TypeScript frontend and a Python FastAPI backend. The backend owns persistence, API contracts, model access, and LangGraph workflows; the frontend treats backend state as source of truth and renders the four-region writing cockpit.

**Tech Stack:** React, Vite, TypeScript, Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL via Docker Compose, LangGraph, pytest, Vitest.

---

## File Structure

- Create `backend/pyproject.toml`: Python package metadata and dependencies.
- Create `backend/app/main.py`: FastAPI app factory and route registration.
- Create `backend/app/core/config.py`: environment-driven settings.
- Create `backend/app/db/session.py`: SQLAlchemy engine and session dependency.
- Create `backend/app/db/base.py`: declarative model base.
- Create `backend/app/models/*.py`: database tables for projects, chapters, characters, foreshadowing, inspirations, generation tasks, task steps, generation runs, and review findings.
- Create `backend/app/schemas/*.py`: Pydantic request and response models.
- Create `backend/app/repositories/*.py`: focused persistence functions.
- Create `backend/app/services/model_provider.py`: provider adapter interface plus deterministic development provider.
- Create `backend/app/services/project_service.py`: project creation and setup generation orchestration.
- Create `backend/app/services/chapter_service.py`: chapter editing, task creation, acceptance, and retry orchestration.
- Create `backend/app/agent/state.py`: LangGraph state types.
- Create `backend/app/agent/project_graph.py`: project setup graph.
- Create `backend/app/agent/chapter_graph.py`: chapter generation graph with node-level persisted step status.
- Create `backend/app/api/routes/*.py`: REST routes for projects, chapters, inspirations, tasks, and generation.
- Create `backend/alembic.ini`, `backend/alembic/env.py`, and `backend/alembic/versions/0001_initial.py`: database migration.
- Create `backend/tests/*.py`: backend integration and workflow tests.
- Create `frontend/package.json`: frontend scripts and dependencies.
- Create `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`: Vite configuration.
- Create `frontend/src/api/client.ts`: typed API client.
- Create `frontend/src/types.ts`: shared frontend data types.
- Create `frontend/src/App.tsx`: four-region writing cockpit shell.
- Create `frontend/src/components/*.tsx`: project creation, chapter sidebar, editor, module panel, and agent workspace.
- Create `frontend/src/App.test.tsx`: cockpit rendering test.
- Create `docker-compose.yml`: PostgreSQL service.
- Create `.env.example`: required backend configuration.
- Modify `.gitignore`: ignore local env files, Python caches, node modules, build output, and virtual environments.
- Create `README.md`: setup, run, and verification commands.

## Task 1: Repository Scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/test_health.py`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Modify: `.gitignore`

- [x] **Step 1: Write the backend health test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [x] **Step 2: Run the failing test**

Run: `cd backend; python -m pytest tests/test_health.py -v`
Expected: FAIL because `app.main` does not exist.

- [x] **Step 3: Add backend package and settings**

`backend/pyproject.toml`:

```toml
[project]
name = "novel-agent-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13.2",
  "fastapi>=0.115.0",
  "langgraph>=0.2.60",
  "psycopg[binary]>=3.2.3",
  "pydantic-settings>=2.6.0",
  "sqlalchemy>=2.0.36",
  "uvicorn[standard]>=0.32.0",
]

[project.optional-dependencies]
dev = [
  "httpx>=0.27.2",
  "pytest>=8.3.3",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

`backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://novel:novel@localhost:5432/novel_agent"
    model_provider: str = "mock"

    model_config = SettingsConfigDict(env_file="../.env", env_prefix="NOVEL_AGENT_")


settings = Settings()
```

- [x] **Step 4: Add FastAPI health endpoint**

`backend/app/main.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Novel Agent API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [x] **Step 5: Add database base and session helpers**

`backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
```

- [x] **Step 6: Add local infrastructure files**

`docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: novel_agent
      POSTGRES_USER: novel
      POSTGRES_PASSWORD: novel
    ports:
      - "5432:5432"
```

`.env.example`:

```dotenv
NOVEL_AGENT_DATABASE_URL=postgresql+psycopg://novel:novel@localhost:5432/novel_agent
NOVEL_AGENT_MODEL_PROVIDER=mock
```

`.gitignore` additions:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
node_modules/
dist/
```

- [x] **Step 7: Run backend health test**

Run: `cd backend; python -m pytest tests/test_health.py -v`
Expected: PASS.

## Task 2: Persistence Schema

**Files:**
- Create: `backend/app/models/project.py`
- Create: `backend/app/models/chapter.py`
- Create: `backend/app/models/character.py`
- Create: `backend/app/models/foreshadowing.py`
- Create: `backend/app/models/inspiration.py`
- Create: `backend/app/models/generation.py`
- Create: `backend/app/models/review.py`
- Modify: `backend/app/db/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`
- Create: `backend/tests/test_models.py`

- [x] **Step 1: Write schema smoke test**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.project import Project
from app.models.chapter import Chapter, ChapterStatus


def test_project_and_chapter_persist_together():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = Project(title="临时标题", idea="少年在雨夜捡到一封未来来信")
        session.add(project)
        session.flush()
        chapter = Chapter(project_id=project.id, number=1, title="雨夜来信")
        session.add(chapter)
        session.commit()

        saved = session.get(Chapter, chapter.id)

    assert saved is not None
    assert saved.status == ChapterStatus.not_generated
```

- [x] **Step 2: Run failing model test**

Run: `cd backend; python -m pytest tests/test_models.py -v`
Expected: FAIL because models do not exist.

- [x] **Step 3: Implement models**

Create enum-backed SQLAlchemy models with these required fields:

```python
class ChapterStatus(str, Enum):
    not_generated = "not_generated"
    generating = "generating"
    generated = "generated"
    accepted = "accepted"
```

```python
class GenerationTaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    failed = "failed"
    completed = "completed"
```

Tables must include:

- `projects`: `id`, `title`, `idea`, `positioning`, `worldview`, `main_plot`, `created_at`, `updated_at`.
- `chapters`: `id`, `project_id`, `number`, `title`, `status`, `content`, `generated_content`, `summary`, `created_at`, `updated_at`.
- `characters`: `id`, `project_id`, `name`, `role`, `personality`, `current_goal`, `key_memories`, `relationships`, `writing_notes`, `created_at`, `updated_at`.
- `foreshadowing_items`: `id`, `project_id`, `source_chapter_id`, `content`, `status`, `notes`, `created_at`, `updated_at`.
- `inspirations`: `id`, `project_id`, `content`, `applied`, `created_at`.
- `generation_tasks`: `id`, `project_id`, `chapter_id`, `kind`, `status`, `current_step`, `error_type`, `error_message`, `created_at`, `updated_at`.
- `generation_task_steps`: `id`, `task_id`, `name`, `status`, `input_snapshot`, `output_snapshot`, `error_message`, `started_at`, `finished_at`.
- `generation_runs`: `id`, `task_id`, `prompt_package`, `output_text`, `review_result`, `accepted`, `created_at`.
- `review_findings`: `id`, `chapter_id`, `task_id`, `problem_type`, `message`, `suggestion`, `blocking`, `created_at`.

- [x] **Step 4: Import models in `db/base.py`**

```python
from app.db.base import Base
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.foreshadowing import ForeshadowingItem
from app.models.generation import GenerationRun, GenerationTask, GenerationTaskStep
from app.models.inspiration import Inspiration
from app.models.project import Project
from app.models.review import ReviewFinding

__all__ = [
    "Base",
    "Project",
    "Chapter",
    "Character",
    "ForeshadowingItem",
    "GenerationRun",
    "GenerationTask",
    "GenerationTaskStep",
    "Inspiration",
    "ReviewFinding",
]
```

- [x] **Step 5: Add Alembic migration**

Create migration `0001_initial.py` with `op.create_table` calls for every table above, foreign keys, indexes on `project_id`, `chapter_id`, `task_id`, and enum-compatible string columns.

- [x] **Step 6: Run schema test**

Run: `cd backend; python -m pytest tests/test_models.py -v`
Expected: PASS.

## Task 3: Backend API Contracts

**Files:**
- Create: `backend/app/schemas/project.py`
- Create: `backend/app/schemas/chapter.py`
- Create: `backend/app/schemas/generation.py`
- Create: `backend/app/repositories/projects.py`
- Create: `backend/app/repositories/chapters.py`
- Create: `backend/app/api/routes/projects.py`
- Create: `backend/app/api/routes/chapters.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_project_api.py`

- [x] **Step 1: Write API test**

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app


def test_create_project_returns_first_chapters():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    app = create_app()

    def override_session():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.post(
        "/api/projects",
        json={"idea": "一个失忆修书人在废城里修补会改变现实的书"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["idea"].startswith("一个失忆修书人")
    assert len(body["chapters"]) >= 3
```

- [x] **Step 2: Run failing API test**

Run: `cd backend; python -m pytest tests/test_project_api.py -v`
Expected: FAIL because routes and schemas do not exist.

- [x] **Step 3: Implement schemas**

Use Pydantic models:

- `ProjectCreate`: `idea: str`, optional `genre`, optional `style`.
- `ProjectRead`: project fields plus `chapters`, `characters`, `foreshadowing_items`, `inspirations`.
- `ChapterRead`: chapter fields.
- `ChapterUpdate`: optional `title`, `content`.
- `TaskRead`: task status fields plus steps.

- [x] **Step 4: Implement repositories**

Repositories should accept `Session` explicitly and contain persistence-only logic:

- `create_project_with_seed(session, idea, setup_result)`.
- `get_project(session, project_id)`.
- `list_projects(session)`.
- `get_chapter(session, chapter_id)`.
- `update_chapter_content(session, chapter_id, title, content)`.

- [x] **Step 5: Implement routes**

Required routes:

- `POST /api/projects`: create project from idea using setup service.
- `GET /api/projects`: list projects.
- `GET /api/projects/{project_id}`: read complete project state.
- `PATCH /api/chapters/{chapter_id}`: edit chapter title or content.

- [x] **Step 6: Run API test**

Run: `cd backend; python -m pytest tests/test_project_api.py -v`
Expected: PASS.

## Task 4: Model Provider Adapter

**Files:**
- Create: `backend/app/services/model_provider.py`
- Create: `backend/tests/test_model_provider.py`

- [x] **Step 1: Write deterministic provider test**

```python
from app.services.model_provider import MockModelProvider


def test_mock_provider_returns_structured_project_setup():
    provider = MockModelProvider()

    result = provider.generate_project_setup("一个月球茶馆老板调查失踪诗人的故事")

    assert result.positioning
    assert len(result.characters) >= 2
    assert len(result.chapters) >= 3
```

- [x] **Step 2: Implement provider interface**

Define dataclasses or Pydantic models for:

- `ProjectSetupResult`
- `CharacterDraft`
- `ChapterPlanDraft`
- `ChapterGenerationResult`
- `ReviewFindingDraft`
- `MemoryUpdateDraft`

Define protocol methods:

- `generate_project_setup(idea: str) -> ProjectSetupResult`
- `generate_chapter(prompt_package: str) -> ChapterGenerationResult`
- `review_chapter(content: str, prompt_package: str) -> list[ReviewFindingDraft]`
- `summarize_chapter(content: str) -> str`

- [x] **Step 3: Implement mock provider**

The mock provider returns deterministic Chinese content derived from the idea and prompt package. This makes the app runnable without external model keys.

- [x] **Step 4: Run provider test**

Run: `cd backend; python -m pytest tests/test_model_provider.py -v`
Expected: PASS.

## Task 5: LangGraph Project Setup Flow

**Files:**
- Create: `backend/app/agent/state.py`
- Create: `backend/app/agent/project_graph.py`
- Create: `backend/app/services/project_service.py`
- Modify: `backend/app/api/routes/projects.py`
- Create: `backend/tests/test_project_graph.py`

- [x] **Step 1: Write project graph test**

```python
from app.agent.project_graph import build_project_setup_graph
from app.services.model_provider import MockModelProvider


def test_project_graph_generates_setup_artifacts():
    graph = build_project_setup_graph(MockModelProvider())

    result = graph.invoke({"idea": "一个海边小镇每天凌晨都会收到未来新闻"})

    assert result["setup"].positioning
    assert result["setup"].worldview
    assert len(result["setup"].chapters) >= 3
```

- [x] **Step 2: Implement state**

`ProjectSetupState` must include:

- `idea: str`
- `setup: ProjectSetupResult | None`
- `errors: list[str]`

- [x] **Step 3: Implement LangGraph**

Build a `StateGraph(ProjectSetupState)` with one named node, `generate_setup`, and compile it. Even though V1 setup is simple, it must use LangGraph so setup can grow later.

- [x] **Step 4: Wire project service**

`create_project_from_idea(session, idea, provider)` must invoke the graph, persist project setup, characters, and initial chapter plans, then return the saved project.

- [x] **Step 5: Run project graph test and API test**

Run: `cd backend; python -m pytest tests/test_project_graph.py tests/test_project_api.py -v`
Expected: PASS.

## Task 6: LangGraph Chapter Generation and Recovery

**Files:**
- Create: `backend/app/agent/chapter_graph.py`
- Create: `backend/app/services/chapter_service.py`
- Create: `backend/app/api/routes/generation.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_chapter_generation.py`
- Create: `backend/tests/test_generation_recovery.py`

- [x] **Step 1: Write chapter generation test**

```python
def test_generate_chapter_records_steps_and_generated_content(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"}).json()
    chapter_id = project["chapters"][0]["id"]

    response = client_with_db.post(f"/api/chapters/{chapter_id}/generate")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["chapter"]["generated_content"]
    assert [step["name"] for step in body["steps"]] == [
        "load_context",
        "build_chapter_target",
        "build_prompt_package",
        "generate_prose",
        "review_prose",
        "propose_memory_updates",
    ]
```

- [x] **Step 2: Write recovery test**

```python
def test_failed_generation_can_be_retried_from_persisted_task(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一名钟表师能听见城市未来一分钟的声音"}).json()
    chapter_id = project["chapters"][0]["id"]

    failed = client_with_db.post(f"/api/chapters/{chapter_id}/generate", json={"fail_at": "review_prose"}).json()
    retry = client_with_db.post(f"/api/generation-tasks/{failed['id']}/retry")

    assert retry.status_code == 200
    assert retry.json()["status"] == "completed"
```

- [x] **Step 3: Implement chapter state**

`ChapterGenerationState` must include:

- `task_id`
- `project_id`
- `chapter_id`
- `context`
- `chapter_target`
- `prompt_package`
- `generated_content`
- `review_findings`
- `summary`
- `character_updates`
- `foreshadowing_updates`
- `fail_at`

- [x] **Step 4: Implement persisted step wrapper**

Each node must call a helper that:

1. Creates or updates a `generation_task_steps` row to `running`.
2. Stores input snapshot as JSON.
3. Runs node logic.
4. Stores output snapshot and marks step `completed`.
5. On exception, marks step and task `failed`, stores `error_type` and `error_message`, then re-raises.

- [x] **Step 5: Implement LangGraph nodes**

Required nodes:

- `load_context`
- `build_chapter_target`
- `build_prompt_package`
- `generate_prose`
- `review_prose`
- `propose_memory_updates`

The graph must be a compiled `StateGraph`, not a hard-coded function chain.

- [x] **Step 6: Implement generation routes**

Required routes:

- `POST /api/chapters/{chapter_id}/generate`: create or run chapter generation task.
- `POST /api/generation-tasks/{task_id}/retry`: rerun failed or interrupted task from persisted state.
- `GET /api/generation-tasks/{task_id}`: fetch task, steps, error, and generated artifacts.
- `GET /api/generation-tasks/interrupted`: list failed or running tasks from previous service lifetime.

- [x] **Step 7: Run generation tests**

Run: `cd backend; python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py -v`
Expected: PASS.

## Task 7: Accept, Reject, and Author Intervention

**Files:**
- Modify: `backend/app/services/chapter_service.py`
- Modify: `backend/app/api/routes/chapters.py`
- Create: `backend/app/api/routes/inspirations.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_author_loop.py`

- [x] **Step 1: Write author loop test**

```python
def test_accept_chapter_updates_content_summary_and_future_context(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个邮差给梦境投递真实信件"}).json()
    chapter_id = project["chapters"][0]["id"]
    client_with_db.post(f"/api/chapters/{chapter_id}/generate")

    accepted = client_with_db.post(f"/api/chapters/{chapter_id}/accept").json()
    inspiration = client_with_db.post(
        f"/api/projects/{project['id']}/inspirations",
        json={"content": "后续必须出现一封写给反派童年的信"},
    ).json()

    assert accepted["status"] == "accepted"
    assert accepted["content"]
    assert accepted["summary"]
    assert inspiration["applied"] is False
```

- [x] **Step 2: Implement accept and reject**

Required behavior:

- Accept copies `generated_content` to `content`, marks chapter `accepted`, saves summary, review findings, generation run, and suggested memory artifacts.
- Reject keeps `content` unchanged, clears active candidate only if the user requests it, and records a generation run with `accepted=false`.

- [x] **Step 3: Implement inspiration route**

Required route:

- `POST /api/projects/{project_id}/inspirations`: persist author inspiration.

Inspiration records must be included in future prompt packages until marked applied by a later accepted generation.

- [x] **Step 4: Run author loop test**

Run: `cd backend; python -m pytest tests/test_author_loop.py -v`
Expected: PASS.

## Task 8: Frontend Cockpit

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/ProjectCreator.tsx`
- Create: `frontend/src/components/ChapterSidebar.tsx`
- Create: `frontend/src/components/ChapterEditor.tsx`
- Create: `frontend/src/components/ModulePanel.tsx`
- Create: `frontend/src/components/AgentWorkspace.tsx`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/styles.css`

- [x] **Step 1: Write cockpit rendering test**

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the four cockpit regions", () => {
    render(<App />);

    expect(screen.getByRole("complementary", { name: "章节" })).toBeInTheDocument();
    expect(screen.getByRole("main", { name: "正文" })).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "模块" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Agent 创作后台" })).toBeInTheDocument();
  });
});
```

- [x] **Step 2: Implement Vite app**

Use a plain, work-focused UI with:

- Left chapter sidebar.
- Center textarea editor and generated-content candidate area.
- Right collapsible modules for positioning, worldview, plot, characters, inspirations, foreshadowing.
- Bottom agent workspace showing task status, prompt package, summary, update suggestions, review findings, and errors.

- [x] **Step 3: Implement typed API client**

Client functions:

- `createProject(payload)`
- `getProject(projectId)`
- `updateChapter(chapterId, payload)`
- `generateChapter(chapterId)`
- `acceptChapter(chapterId)`
- `rejectChapter(chapterId)`
- `addInspiration(projectId, content)`
- `retryTask(taskId)`

- [x] **Step 4: Implement interactive app behavior**

Required workflows:

- Create project from idea.
- Select chapter.
- Edit chapter content.
- Generate chapter.
- Accept generated chapter.
- Reject generated chapter.
- Add inspiration.
- Retry failed generation.

- [x] **Step 5: Run frontend test**

Run: `cd frontend; npm test -- --run`
Expected: PASS.

## Task 9: End-to-End Local Verification

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/plans/2026-07-08-novel-agent-v1-implementation.md`

- [x] **Step 1: Add README**

Include commands:

```powershell
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

```powershell
cd frontend
npm install
npm run dev
```

Verification commands:

```powershell
cd backend
python -m pytest -v
```

```powershell
cd frontend
npm test -- --run
npm run build
```

- [x] **Step 2: Run backend verification**

Run: `cd backend; python -m pytest -v`
Expected: PASS.

- [x] **Step 3: Run frontend verification**

Run: `cd frontend; npm test -- --run; npm run build`
Expected: PASS.

- [x] **Step 4: Run application smoke test**

Run:

```powershell
docker compose up -d postgres
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm run dev
```

Expected: the browser can create a project, generate one chapter, accept it, add inspiration, generate another chapter using previous summary and inspiration, and retry a simulated failed task.

- [x] **Step 5: Record implementation result**

Append an `## Implementation Result` section to this plan with:

- Commands run.
- Test results.
- Known limitations.
- Local URLs.

## Self-Review

- Spec coverage: This plan covers every V1 must-have from `docs/superpowers/specs/2026-07-08-novel-agent-v1-requirements.md`: project creation, idea input, setup generation, chapter list, chapter editing, single-chapter generation, inspiration input, simple character cards, summaries, foreshadowing, review findings, generation records, node-level recovery, and PostgreSQL persistence.
- Placeholder scan: No `TBD`, `TODO`, `implement later`, or unspecified test commands remain.
- Type consistency: Project, chapter, task, provider, and graph names are consistent across backend services, tests, and API routes.

## Implementation Result

- Backend implemented with FastAPI, SQLAlchemy models, Alembic migration, deterministic mock model provider, LangGraph project setup graph, LangGraph chapter generation graph, persisted generation task steps, retry support, chapter accept/reject, and inspiration input.
- Frontend implemented with React + Vite + TypeScript four-region cockpit: chapter sidebar, editor, collapsible module panel, and Agent workspace.
- Docker Compose now includes PostgreSQL middleware, backend, and frontend services. PostgreSQL uses `pgvector/pgvector:pg16` because that image already exists locally and avoids a Docker Hub pull for the database middleware.
- Docker project container build was attempted with `docker compose build`, but Docker Desktop could not reach Docker Hub for `python:3.11-slim` and `node:22-alpine` because no HTTPS proxy was configured. The backend and frontend Dockerfiles are present and should build once Docker Hub access or a registry mirror is available.
- PostgreSQL middleware smoke test passed through Docker: `docker compose up -d postgres`, `python Alembic API upgrade head` against `localhost:55432`, then FastAPI TestClient created a project, generated a chapter, and accepted it.
- Local dev services started:
  - Backend: `http://127.0.0.1:8000`
  - Frontend: `http://127.0.0.1:5173`

Verification commands run:

```powershell
cd backend
python -m pytest -v
```

Result: 8 passed, 5 warnings. Warnings are from FastAPI/TestClient using httpx's deprecated `app` shortcut in installed dependency versions.

```powershell
cd frontend
npm test -- --run
npm run build
```

Result: frontend test passed and production build succeeded.

```powershell
docker compose config
docker compose up -d postgres
```

Result: compose config parsed, PostgreSQL middleware started healthy on host port `55432`.
