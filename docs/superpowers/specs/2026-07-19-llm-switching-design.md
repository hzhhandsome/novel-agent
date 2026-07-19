# LLM Switching Design

## Goal

Add first-stage smooth LLM switching: users can change the global runtime model, new generation tasks use the new model, and existing tasks keep their creation-time model snapshot.

## Scope

This design covers:

- Backend runtime model config API.
- Task-level model config snapshots.
- Generation run model config snapshots.
- Retry using the original task snapshot.
- Frontend control for provider, base URL, model, max tokens, and optional API key update.

This does not add project-level model config, node-level model routing, cost tracking, prompt versioning, or persistent secret storage.

## Architecture

`backend/app/services/provider_factory.py` remains the boundary for creating provider instances. It will gain:

- `ModelConfigSnapshot`.
- `get_current_model_config()`.
- `update_runtime_model_config()`.
- `get_model_config_snapshot()`.
- `get_model_provider_from_snapshot()`.

`GenerationTask` and `GenerationRun` gain `model_config_snapshot` JSON columns. Chapter generation creates a snapshot when the task is created. Retries and persisted runs reuse that snapshot.

`backend/app/api/routes/generation.py` exposes:

- `GET /api/model-config`
- `PUT /api/model-config`

The API never returns the API key value. It only returns `api_key_set`.

## Data Flow

1. Frontend loads current model config.
2. User changes provider/base URL/model/max tokens/API key.
3. Backend updates only the current process runtime config.
4. A new generation task snapshots the current runtime config.
5. The graph builds provider from the task snapshot.
6. Retry reads the existing task snapshot, ignoring later runtime switches.
7. `GenerationRun` stores the task snapshot for later review.

## Tests

Backend:

- Model config API switches runtime config and never returns the secret.
- New generation task stores the active snapshot.
- Retrying an old failed task uses the task snapshot even after runtime config changes.

Frontend:

- Model controls render current config.
- Saving model config calls the API.

