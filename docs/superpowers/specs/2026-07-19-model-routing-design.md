# Model Routing Design

## Goal

Add first-stage node-level model routing for chapter generation while preserving task reproducibility.

## Scope

P0 covers three route keys:

- `generation`: used by `generate_prose`.
- `audit`: used by `audit_prose`.
- `summary`: used by `summarize_chapter`.

All other LangGraph nodes use the task default model snapshot.

## Behavior

- Global model config remains the default route.
- `GET /api/model-config` returns default config plus optional `routes`.
- `PUT /api/model-config` can update default config and route overrides.
- A route override may set provider, base URL, model, and max tokens.
- API keys are not returned and are not written to snapshots.
- New generation tasks snapshot both default config and route overrides.
- Retry uses the task snapshot, including route overrides, even if global config changed later.
- If a route is missing, that node uses the task default provider.

## Frontend

The existing model toolbar remains compact. Add three optional model-name fields:

- 生成模型
- 审核模型
- 摘要模型

Leaving a field empty clears that route override. In the first stage these fields inherit the current default provider, base URL, and max token setting. More detailed per-route provider/base URL controls stay out of P0 UI to avoid toolbar bloat.

## Observability

The routed nodes include their route key and public model config in node output snapshots. `GenerationTask.model_config_snapshot` remains the task-level source of truth for reproducing routing decisions.

## Tests

- Backend API returns and updates route config without exposing secrets.
- Generation uses different providers for generation/audit/summary route keys.
- Retry uses task route snapshot after global routing changes.
- Frontend saves route model fields through `PUT /api/model-config`.

## Non-Goals

- Project-level routing.
- Per-route API keys.
- Full UI for route provider/base URL/max tokens.
- Routing every LangGraph node.
