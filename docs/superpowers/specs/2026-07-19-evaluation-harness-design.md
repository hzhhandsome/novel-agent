# Evaluation Harness Design

## Goal

Add a first P0 eval harness for two quality checks: summary fact retention and audit conflict detection.

## Scope

This design covers deterministic offline evaluation:

- Evaluate whether a chapter summary preserves expected facts.
- Evaluate whether audit findings detect expected conflicts.
- Maintain a small built-in gold case set for regression checks.
- Provide a runnable module command for local replay.
- Document how later prompt/model/RAG changes can compare against the same eval cases.

This does not add a UI, persistent eval database, LLM-as-judge, precision/F1 dashboards, or automatic eval execution after every generation.

## Architecture

`backend/app/services/evaluation.py` owns pure eval functions:

- `ExpectedItem`: one expected fact/conflict with aliases.
- `evaluate_summary_fact_retention(summary, expected_facts)`.
- `evaluate_audit_conflict_detection(findings, expected_conflicts)`.

`backend/app/evals/gold_cases.py` owns a small built-in case set:

- Summary cases with summary text and expected facts.
- Audit cases with finding text and expected conflicts.

`backend/app/evals/run.py` provides:

```powershell
python -m app.evals.run
```

It prints JSON with per-case results and aggregate rates.

## Matching Policy

First-stage eval uses deterministic text matching:

- An expected item is detected if its label or any alias appears in the output text.
- Summary retention rate = detected facts / expected facts.
- Audit conflict recall = detected conflicts / expected conflicts.
- A case passes if the rate is at least its threshold.

This is intentionally simple and repeatable. Later versions can add LLM judge, embeddings, precision, recall, F1, and false-positive tracking.

## Tests

Backend tests:

- Verify summary fact retention counts retained/missing facts.
- Verify audit conflict detection counts detected/missed conflicts.
- Verify built-in eval runner returns aggregate metrics.

