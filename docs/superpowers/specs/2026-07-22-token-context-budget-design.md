# Tokenizer Context Budget Design

## Goal

Upgrade context budgeting from fixed character sizing to token-oriented estimates while keeping the chapter generation flow unchanged and lightweight.

## Scope

This first stage adds a shared token counting service, uses it in `load_context`, and updates the Agent backend UI to label context usage as estimated tokens. It does not add provider token-count APIs, new LangGraph nodes, online tokenizer downloads as a hard dependency, or user-facing tokenizer configuration controls.

## Design

- Add `backend/app/services/token_counter.py`.
- The counter tries a local Hugging Face tokenizer when `NOVEL_AGENT_TOKENIZER_PROVIDER=transformers`.
- If the tokenizer cannot be imported or loaded, it falls back to the deterministic character heuristic.
- The fallback remains deterministic for tests and local development.
- `model_usage.estimate_tokens()` delegates to the shared counter so usage and context budget use one estimate path.

## Context Budget Fields

`load_context.context_budget` records:

- `model_max_tokens`
- `reserved_output_tokens`
- `fixed_prompt_reserve_tokens`
- `context_budget_tokens`
- `estimated_tokens`
- `estimated_chars`
- `counter_name`
- `is_fallback`
- per-section token and character usage

Existing compatibility fields remain:

- `total_budget`
- `used`
- `sections[].budget`
- `sections[].used`

These compatibility fields now represent token estimates instead of character counts.

## Budget Rules

The active budget is derived from the task model config snapshot:

- `model_max_tokens` comes from the task snapshot, falling back to settings.
- `reserved_output_tokens` reserves output capacity.
- `fixed_prompt_reserve_tokens` reserves system prompt, chapter target, and fixed setup capacity.
- `context_budget_tokens` is the remaining active budget for variable long-term context.

Section budgets are allocated proportionally from the active context budget using the existing section weights.

## UI

The Agent backend header displays context usage as:

`上下文 1200 / 3000 tokens（估算，fallback）`

The context tab displays per-section included and omitted counts, estimated token usage, estimated character usage, and omitted summaries.

## Acceptance

- A generation task shows estimated context tokens and characters.
- Changing `model_max_tokens` changes reserved and active context budget in the task snapshot.
- If a tokenizer is unavailable, generation still works and marks the report as fallback.
- Existing chapter generation and frontend tests still pass.
