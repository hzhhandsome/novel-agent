# Tokenizer Context Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tokenizer-oriented context budgeting to chapter generation and expose the estimate clearly in the Agent backend.

**Architecture:** A new shared token counter service provides local tokenizer counting with deterministic fallback. `load_context` uses dynamic token budgets derived from the task model config snapshot, while preserving legacy report fields for existing consumers.

**Tech Stack:** Python, FastAPI service layer, LangGraph chapter flow, pytest, React/Vite, Vitest.

---

## Read Context

- Read: `docs/modules/generation-flow.md`
- Read: `docs/modules/model-provider.md`
- Read: `docs/product/roadmap.md`

## Files

- Create: `backend/app/services/token_counter.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/model_usage.py`
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/tests/test_context_budget.py`
- Create: `backend/tests/test_token_counter.py`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `.env.example`
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/product/roadmap.md`

## Tasks

- [x] Add failing tests for token counter fallback and injected tokenizer counting.
- [x] Implement `token_counter` with fallback metadata.
- [x] Add failing tests for context budget token fields and dynamic model max token budget.
- [x] Update `chapter_graph` to pass the model config snapshot into `load_context` and budget by token estimates.
- [x] Update model usage to reuse the shared token counter.
- [x] Add/update frontend tests for the estimated token budget label.
- [x] Update Agent backend context budget formatting.
- [x] Update config examples and module docs.
- [ ] Run backend and frontend verification.
- [ ] Commit and push code changes with a Chinese message.

## Implementation Result

- Added `backend/app/services/token_counter.py`.
- `load_context.context_budget` now records estimated token/char usage, model max tokens, output reserve, fixed prompt reserve, context budget tokens, counter name, and fallback status.
- Agent backend displays `tokens（估算）` and fallback metadata.
