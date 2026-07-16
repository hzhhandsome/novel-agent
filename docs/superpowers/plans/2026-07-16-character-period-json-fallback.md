# Character Period JSON Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent invalid LLM JSON from the non-critical character-period judgment node from aborting chapter generation.

**Architecture:** Keep `generate_prose`, `audit_prose`, and `summarize_chapter` strict because they define the candidate draft and acceptance boundary. Add a local fallback only around `judge_character_period`, returning a structured skipped result with the error message so downstream candidate aggregation and SSE display can continue.

**Tech Stack:** FastAPI, LangGraph, pytest, existing `ModelProvider` protocol.

---

## Files

- Modify `backend/tests/test_chapter_generation.py`: add a regression test with a provider whose `judge_character_period` raises `ValueError("Expecting ',' delimiter...")`.
- Modify `backend/app/agent/chapter_graph.py`: catch exceptions in `_judge_character_period` and return a structured fallback decision.
- Modify `docs/modules/generation-flow.md`: document non-critical judgment node fallback behavior.

---

## Tasks

- [ ] Write failing regression test.
- [ ] Run targeted test and confirm it fails because the graph aborts at `judge_character_period`.
- [ ] Implement fallback in `_judge_character_period`.
- [ ] Run targeted backend tests.
- [ ] Update module docs.
- [ ] Run full backend/frontend verification.
- [ ] Commit and push.

## Self-Review

- Scope coverage: Covers the observed node 8 invalid JSON failure.
- Scope control: Does not hide failures from prose generation, audit, summary, persistence, or database writes.
- Data shape: Fallback returns `updates`, `new_period_cards`, `relationship_changes`, `memory_changes`, `stage_changed`, `skipped`, and `error`.

## Implementation Result

- Added regression test for invalid JSON failure in `judge_character_period`.
- Wrapped only the character-period judgment provider call with a structured fallback.
- Fallback records `skipped=true` and the original error string in `character_period_decisions`.
- Updated generation-flow module docs with the non-critical fallback boundary.

Focused verification:

- `python -m pytest tests/test_chapter_generation.py::test_character_period_json_failure_does_not_abort_generation -v`: 1 passed.
- `python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py tests/test_auto_generation.py -v`: 6 passed.
