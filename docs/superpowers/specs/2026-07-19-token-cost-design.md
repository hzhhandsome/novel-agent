# Token Cost Tracking Design

## Goal

Record first-stage usage metrics for model calls so generation quality, context budget, routing, and cost decisions have data.

## Scope

Track usage for chapter generation model-call nodes:

- `generate_prose`
- `audit_prose`
- `summarize_chapter`
- `judge_foreshadowing`
- `judge_character_period`
- `propose_future_plan_updates`

Project setup usage can be added later.

## Behavior

- Each model-call node records estimated input tokens, estimated output tokens, elapsed milliseconds, estimated cost, route key, and public model config.
- If a provider later returns actual token usage, it can replace the estimate behind the same shape.
- Token estimates use a deterministic local heuristic so tests do not depend on provider usage metadata.
- Cost uses configurable per-1k-token prices with zero defaults.
- `GenerationRun` stores an aggregate usage snapshot when a candidate is accepted or rejected.
- Agent backstage displays total estimated tokens and cost for the current task.

## Non-Goals

- Exact tokenizer integration.
- Live billing-provider price sync.
- Provider-specific usage parsing.
- Project creation usage tracking.
