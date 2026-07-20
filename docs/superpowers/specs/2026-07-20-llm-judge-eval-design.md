# LLM-as-judge Eval Design

## Goal

Add a lightweight offline LLM-as-judge evaluation path so the project can demonstrate rubric-based semantic evaluation without slowing or destabilizing the 11-node chapter generation flow.

## Scope

- Extend built-in Eval with a `judge` section.
- Use small deterministic judge cases stored in code.
- Support real provider execution through a dedicated provider method.
- Keep a mock judge implementation for tests and local runs.
- Show judge metrics in the existing frontend Eval panel.
- Record judge prompt version so results can be compared across prompt/rubric changes.

Out of scope:

- Do not insert judge into chapter generation nodes.
- Do not write judge results to the database.
- Do not add an Eval history page.
- Do not auto-train or auto-change prompts from judge results.

## Architecture

`backend/app/evals/judge_cases.py` defines fixed cases with text, context, rubric and thresholds. `backend/app/services/evaluation.py` exposes pure aggregation helpers for judge scores. `ModelProvider` gains `judge_eval_case(case)` and returns a structured `JudgeEvalResult`. `run_builtin_evals()` runs cases through the current provider and adds a `judge` report beside summary, audit and RAG.

The frontend keeps using `GET /api/evals/builtin`. `BuiltinEvalReport` receives an optional `judge` section and `AgentWorkspace` renders average semantic score, pass count, failed cases and blocking findings.

## Data Shape

Each judge case contains:

- `case_id`
- `name`
- `input_text`
- `context`
- `rubric`
- `threshold`

Each judge result contains:

- `metric = "llm_judge"`
- `case_id`
- `case`
- `prompt_version`
- `scores`: `consistency`, `character`, `foreshadowing`, `style`
- `average_score`
- `blocking_findings`
- `reason`
- `passed`

## Error Handling

If a real provider returns malformed judge JSON, the provider raises the same parsing error style as other model calls. Built-in Eval remains a developer tool, so the first stage should fail visibly instead of hiding broken judge output.

## Testing

- Unit test judge score aggregation.
- Unit test built-in Eval report includes `judge`.
- Unit test mock provider judge result.
- Unit test DeepSeek provider parses judge JSON.
- Frontend test/build verifies Eval UI still compiles with the new optional section.
