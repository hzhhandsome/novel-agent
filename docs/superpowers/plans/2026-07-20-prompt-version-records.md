# Prompt Version Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record prompt template versions, prompt hashes, and context builder version in generation node snapshots and expose prompt-version grouping in the built-in Eval report.

**Architecture:** Avoid a schema migration for the first phase. Store prompt metadata in existing `GenerationTaskStep.output_snapshot` JSON and aggregate accepted/rejected `GenerationRun.model_usage_snapshot.prompt_versions`; add deterministic helpers so future prompt comparisons can reuse the same fields.

**Tech Stack:** Python dataclasses/hashlib, LangGraph node snapshots, pytest, existing FastAPI eval endpoint, React/Vitest backstage display.

---

## Context Read

- Read `docs/modules/generation-flow.md`: `build_prompt_package` builds the prose prompt package, model nodes store output snapshots and usage, `GenerationRun` stores prompt package and usage snapshot.
- Read `docs/modules/model-provider.md`: model-call nodes already record model route config and usage in output snapshots.
- Read `docs/modules/evaluation.md`: built-in Eval runner now returns summary, audit, RAG, and overall metrics.

## Files

- Create: `backend/app/services/prompt_versions.py`
  - Own stable prompt template versions, context builder version, prompt hashing, and metadata extraction.
- Modify: `backend/app/agent/state.py`
  - Add prompt metadata keys to chapter generation state.
- Modify: `backend/app/agent/chapter_graph.py`
  - Attach prompt metadata to `build_prompt_package` and model/judgment nodes.
- Modify: `backend/app/services/chapter_service.py`
  - Aggregate prompt versions into `GenerationRun.model_usage_snapshot`.
- Modify: `backend/app/evals/run.py`
  - Add prompt-version grouping for built-in Eval report.
- Modify: `backend/tests/test_prompt_versions.py`
  - New tests for stable hashing and eval grouping.
- Modify: `backend/tests/test_chapter_generation.py`
  - Assert generation node snapshots include prompt metadata.
- Modify: `backend/tests/test_model_usage.py`
  - Assert accepted run stores prompt version aggregate.
- Modify: `frontend/src/types.ts`
  - Add optional prompt-version report shape.
- Modify: `frontend/src/components/AgentWorkspace.tsx`
  - Show prompt version details in selected flow node.
- Modify: `frontend/src/App.test.tsx`
  - Assert prompt version appears in backstage details and Eval report grouping.
- Modify: `docs/modules/generation-flow.md`
  - Document prompt metadata fields.
- Modify: `docs/modules/model-provider.md`
  - Document prompt version snapshots beside model usage.
- Modify: `docs/modules/evaluation.md`
  - Document Eval `prompt_versions` grouping.

### Task 1: Prompt Metadata Service

**Files:**
- Create: `backend/tests/test_prompt_versions.py`
- Create: `backend/app/services/prompt_versions.py`

- [x] **Step 1: Write failing prompt metadata test**

Create `backend/tests/test_prompt_versions.py`:

```python
from app.services.prompt_versions import CONTEXT_BUILDER_VERSION, prompt_metadata


def test_prompt_metadata_uses_stable_version_and_hash():
    first = prompt_metadata("generate_prose", "写一章正文")
    second = prompt_metadata("generate_prose", "写一章正文")

    assert first["prompt_template"] == "generate_prose"
    assert first["prompt_version"] == "generate_prose@2026-07-20.v1"
    assert first["context_builder_version"] == CONTEXT_BUILDER_VERSION
    assert first["prompt_hash"] == second["prompt_hash"]
    assert len(first["prompt_hash"]) == 64
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py -v
```

Expected: FAIL because `app.services.prompt_versions` does not exist.

- [x] **Step 3: Implement metadata service**

Create `backend/app/services/prompt_versions.py`:

```python
from __future__ import annotations

import hashlib
from typing import Any

CONTEXT_BUILDER_VERSION = "context_builder@2026-07-20.v1"

PROMPT_TEMPLATE_VERSIONS = {
    "build_prompt_package": "build_prompt_package@2026-07-20.v1",
    "generate_prose": "generate_prose@2026-07-20.v1",
    "audit_prose": "audit_prose@2026-07-20.v1",
    "summarize_chapter": "summarize_chapter@2026-07-20.v1",
    "judge_foreshadowing": "judge_foreshadowing@2026-07-20.v1",
    "judge_character_period": "judge_character_period@2026-07-20.v1",
    "propose_future_plan_updates": "propose_future_plan_updates@2026-07-20.v1",
    "builtin_eval": "builtin_eval@2026-07-20.v1",
}


def prompt_metadata(node: str, prompt_text: str) -> dict[str, str]:
    return {
        "prompt_template": node,
        "prompt_version": PROMPT_TEMPLATE_VERSIONS.get(node, f"{node}@unversioned"),
        "prompt_hash": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        "context_builder_version": CONTEXT_BUILDER_VERSION,
    }


def collect_prompt_versions(step_snapshots: list[dict[str, Any] | None]) -> dict[str, Any]:
    versions: dict[str, dict[str, str]] = {}
    for snapshot in step_snapshots:
        if not snapshot:
            continue
        for key, value in snapshot.items():
            if key == "prompt_metadata" and isinstance(value, dict):
                _add_prompt_version(versions, str(value.get("prompt_template") or "unknown"), value)
            if key.endswith("_prompt_metadata") and isinstance(value, dict):
                _add_prompt_version(versions, key[: -len("_prompt_metadata")], value)
    return {
        "context_builder_version": CONTEXT_BUILDER_VERSION,
        "nodes": versions,
    }


def _add_prompt_version(target: dict[str, dict[str, str]], node: str, value: dict[str, Any]) -> None:
    target[node] = {
        "prompt_template": str(value.get("prompt_template") or node),
        "prompt_version": str(value.get("prompt_version") or ""),
        "prompt_hash": str(value.get("prompt_hash") or ""),
        "context_builder_version": str(value.get("context_builder_version") or CONTEXT_BUILDER_VERSION),
    }
```

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py -v
```

Expected: PASS.

### Task 2: Generation Snapshots and Run Aggregate

**Files:**
- Modify: `backend/app/agent/state.py`
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/app/services/chapter_service.py`
- Modify: `backend/tests/test_chapter_generation.py`
- Modify: `backend/tests/test_model_usage.py`

- [x] **Step 1: Write failing generation snapshot test**

Add to `test_generate_chapter_records_steps_and_generated_content` in `backend/tests/test_chapter_generation.py`:

```python
    prompt_step = next(step for step in body["steps"] if step["name"] == "build_prompt_package")
    generate_step = next(step for step in body["steps"] if step["name"] == "generate_prose")
    audit_step = next(step for step in body["steps"] if step["name"] == "audit_prose")

    assert prompt_step["output_snapshot"]["prompt_metadata"]["prompt_version"].startswith("build_prompt_package@")
    assert generate_step["output_snapshot"]["generate_prose_prompt_metadata"]["prompt_version"].startswith("generate_prose@")
    assert audit_step["output_snapshot"]["audit_prose_prompt_metadata"]["prompt_version"].startswith("audit_prose@")
    assert len(generate_step["output_snapshot"]["generate_prose_prompt_metadata"]["prompt_hash"]) == 64
```

- [x] **Step 2: Write failing GenerationRun aggregate test**

Add to `test_generation_records_node_usage_and_run_aggregate` in `backend/tests/test_model_usage.py`:

```python
    prompt_versions = run.model_usage_snapshot["prompt_versions"]
    assert prompt_versions["nodes"]["generate_prose"]["prompt_version"].startswith("generate_prose@")
    assert prompt_versions["nodes"]["audit_prose"]["prompt_version"].startswith("audit_prose@")
    assert prompt_versions["context_builder_version"].startswith("context_builder@")
```

- [x] **Step 3: Run tests and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content tests/test_model_usage.py::test_generation_records_node_usage_and_run_aggregate -v
```

Expected: FAIL because prompt metadata is not present.

- [x] **Step 4: Attach metadata in chapter graph**

Modify `backend/app/agent/state.py` to add:

```python
    prompt_metadata: dict
    generate_prose_prompt_metadata: dict
    audit_prose_prompt_metadata: dict
    summarize_chapter_prompt_metadata: dict
    judge_foreshadowing_prompt_metadata: dict
    judge_character_period_prompt_metadata: dict
    propose_future_plan_updates_prompt_metadata: dict
```

Modify `backend/app/agent/chapter_graph.py`:

- Import `prompt_metadata`.
- Add the new prompt metadata keys to `_snapshot_state`.
- In `_build_prompt_package`, return `"prompt_metadata": prompt_metadata("build_prompt_package", prompt_package)`.
- In model/judgment nodes, compute input text and return `<node>_prompt_metadata`.

For example in `_generate_prose`:

```python
            "generate_prose_prompt_metadata": prompt_metadata("generate_prose", state["prompt_package"]),
```

Use these prompt texts:

- `generate_prose`: `state["prompt_package"]`
- `audit_prose`: `input_text`
- `summarize_chapter`: generated content input
- `judge_foreshadowing`: `input_text`
- `judge_character_period`: `input_text`
- `propose_future_plan_updates`: `input_text`

- [x] **Step 5: Aggregate into GenerationRun**

Modify `backend/app/services/chapter_service.py`:

- Import `collect_prompt_versions`.
- After `model_usage_snapshot = aggregate_model_usage(...)`, add:

```python
    if model_usage_snapshot is None:
        model_usage_snapshot = {}
    model_usage_snapshot["prompt_versions"] = collect_prompt_versions([step.output_snapshot for step in task.steps])
```

- [x] **Step 6: Run tests and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content tests/test_model_usage.py::test_generation_records_node_usage_and_run_aggregate -v
```

Expected: PASS.

### Task 3: Eval Prompt-Version Grouping

**Files:**
- Modify: `backend/app/evals/run.py`
- Modify: `backend/tests/test_prompt_versions.py`

- [x] **Step 1: Write failing Eval grouping test**

Add to `backend/tests/test_prompt_versions.py`:

```python
from app.evals.run import run_builtin_evals


def test_builtin_eval_report_groups_results_by_prompt_version():
    report = run_builtin_evals()

    assert report["prompt_versions"]["case_count"] == report["overall"]["case_count"]
    assert report["prompt_versions"]["groups"]
    group = report["prompt_versions"]["groups"][0]
    assert group["prompt_version"] == "builtin_eval@2026-07-20.v1"
    assert group["case_count"] == report["overall"]["case_count"]
    assert group["passed_count"] == report["overall"]["passed_count"]
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py::test_builtin_eval_report_groups_results_by_prompt_version -v
```

Expected: FAIL because `prompt_versions` is absent.

- [x] **Step 3: Add grouping to runner**

Modify `backend/app/evals/run.py`:

- Import `PROMPT_TEMPLATE_VERSIONS`.
- When building summary/audit/rag result dictionaries, add:

```python
"prompt_version": PROMPT_TEMPLATE_VERSIONS["builtin_eval"],
```

- Add helper:

```python
def _prompt_version_groups(results: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for item in results:
        version = str(item.get("prompt_version") or "unknown")
        group = groups.setdefault(version, {"prompt_version": version, "case_count": 0, "passed_count": 0})
        group["case_count"] += 1
        if item.get("passed"):
            group["passed_count"] += 1
    return {
        "case_count": len(results),
        "groups": list(groups.values()),
    }
```

- Include `"prompt_versions": _prompt_version_groups(summary_results + audit_results + rag_results)` in the returned report.

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py -v
```

Expected: PASS.

### Task 4: Frontend Display

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend test updates**

In the `runs built-in evals from the backstage and shows the report` mock, add:

```typescript
              prompt_versions: {
                case_count: 5,
                groups: [{ prompt_version: "builtin_eval@2026-07-20.v1", case_count: 5, passed_count: 3 }],
              },
```

Assert:

```typescript
expect(screen.getByText("Prompt 版本 builtin_eval@2026-07-20.v1")).toBeInTheDocument();
```

In `renders real generation step snapshots in the backstage`, add to the `build_prompt_package` output:

```typescript
            prompt_metadata: {
              prompt_template: "build_prompt_package",
              prompt_version: "build_prompt_package@2026-07-20.v1",
              prompt_hash: "abc123",
              context_builder_version: "context_builder@2026-07-20.v1",
            },
```

Assert after clicking the prompt node:

```typescript
expect(screen.getByText("Prompt 版本")).toBeInTheDocument();
expect(screen.getByText(/build_prompt_package@2026-07-20.v1/)).toBeInTheDocument();
```

- [x] **Step 2: Run frontend tests and verify RED**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "built-in evals|real generation step"
```

Expected: FAIL because prompt versions are not displayed.

- [x] **Step 3: Add frontend types and display helpers**

Modify `frontend/src/types.ts`:

```typescript
export interface PromptVersionGroup {
  prompt_version: string;
  case_count: number;
  passed_count: number;
}
```

Add optional field to `BuiltinEvalReport`:

```typescript
  prompt_versions?: {
    case_count: number;
    groups: PromptVersionGroup[];
  };
```

Modify `AgentWorkspace.tsx`:

- Add helper:

```typescript
function formatPromptMetadata(output: Record<string, unknown>): string {
  const metadata = output.prompt_metadata && typeof output.prompt_metadata === "object" && !Array.isArray(output.prompt_metadata)
    ? (output.prompt_metadata as Record<string, unknown>)
    : Object.entries(output)
        .filter(([key, value]) => key.endsWith("_prompt_metadata") && value && typeof value === "object" && !Array.isArray(value))
        .map(([, value]) => value as Record<string, unknown>)[0];
  if (!metadata) return "";
  return [
    stringifyValue(metadata.prompt_version),
    stringifyValue(metadata.context_builder_version),
    stringifyValue(metadata.prompt_hash),
  ].filter(Boolean).join("；");
}
```

- In `stepHighlights`, after usage text:

```typescript
  const promptText = formatPromptMetadata(output);
  if (promptText) items.push(["Prompt 版本", promptText]);
```

- In Eval card metric grid:

```tsx
{evalReport.prompt_versions?.groups[0] ? (
  <span>Prompt 版本 {evalReport.prompt_versions.groups[0].prompt_version}</span>
) : null}
```

- [x] **Step 4: Run frontend tests and verify GREEN**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "built-in evals|real generation step"
```

Expected: PASS.

### Task 5: Docs, Verification, Commit

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/modules/evaluation.md`
- Modify: `docs/superpowers/plans/2026-07-20-prompt-version-records.md`

- [x] **Step 1: Update module docs**

Document:

- `GenerationTaskStep.output_snapshot.prompt_metadata`
- `<node>_prompt_metadata`
- `GenerationRun.model_usage_snapshot.prompt_versions`
- Eval `prompt_versions.groups`

Clarify first phase stores metadata in JSON snapshots, not a dedicated prompt-version table.

- [x] **Step 2: Run targeted verification**

Run:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py tests/test_chapter_generation.py tests/test_model_usage.py tests/test_evaluation.py -v
python -m app.evals.run
cd ..\frontend
npm test -- --run src/App.test.tsx -t "built-in evals|real generation step"
```

Expected: all commands pass.

- [x] **Step 3: Commit and push**

Do not include unrelated pure docs `docs/product/roadmap.md` and `docs/interview/`.

Run:

```powershell
git add backend/app/services/prompt_versions.py backend/app/agent/state.py backend/app/agent/chapter_graph.py backend/app/services/chapter_service.py backend/app/evals/run.py backend/tests/test_prompt_versions.py backend/tests/test_chapter_generation.py backend/tests/test_model_usage.py frontend/src/types.ts frontend/src/components/AgentWorkspace.tsx frontend/src/App.test.tsx docs/modules/generation-flow.md docs/modules/model-provider.md docs/modules/evaluation.md docs/superpowers/plans/2026-07-20-prompt-version-records.md
git commit -m "记录 Prompt 版本和 Eval 分组"
git push
```

Expected: commit and push succeed.

## Self-Review

- Spec coverage: Covers prompt template version, prompt hash, context builder version, node snapshots, run aggregate, Eval grouping, frontend visibility, and module docs.
- Placeholder scan: No TBD/TODO/unspecified steps remain.
- Scope control: No database migration or prompt management UI in this phase.

## Implementation Result

- Added `backend/app/services/prompt_versions.py` for stable prompt versions, context builder version, SHA-256 prompt hash, and prompt version aggregation.
- Added prompt metadata to `build_prompt_package` and six model/judgment nodes.
- Aggregated prompt versions into `GenerationRun.model_usage_snapshot.prompt_versions`.
- Added built-in Eval `prompt_versions.groups` grouped by `builtin_eval@2026-07-20.v1`.
- Added Agent backstage display for selected node Prompt version and Eval prompt-version group.
- Updated generation-flow, model-provider, and evaluation module docs.

Verification completed:

```powershell
cd backend
python -m pytest tests/test_prompt_versions.py tests/test_chapter_generation.py tests/test_model_usage.py tests/test_evaluation.py -v
python -m app.evals.run
cd ..\frontend
npm test -- --run src/App.test.tsx -t "built-in evals|real generation step"
```

