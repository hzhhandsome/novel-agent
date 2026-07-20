# Agent Trace Design

## Goal

Add first-stage Agent observability so each generation task can be inspected as a trace tree covering the task, LangGraph steps, LLM calls, RAG retrieval, tool calls, persistence actions, errors, token estimates, and duration.

## Scope

This stage does not add a trace database table and does not integrate Langfuse, LangSmith, or OpenTelemetry. Trace data is derived from existing persisted `GenerationTask` and `GenerationTaskStep` snapshots, then returned as `task.trace` by generation APIs and SSE task events.

## Architecture

Backend adds a small trace builder service:

- Input: one persisted `GenerationTask`.
- Output: a stable JSON trace object.
- IDs are deterministic:
  - `trace_id = generation-task-{task.id}`
  - root span id: `task-{task.id}`
  - step span id: `step-{step.id}`
  - child event ids derived from step id and event kind.

The trace builder creates:

- a root `task` span;
- one `step` span per `GenerationTaskStep`;
- `llm_call` children for every `<node>_model_usage`;
- `retrieval` children from `context_package.retrieval_results`;
- `tool_call` children from `output_snapshot.tool_calls`;
- `persistence` children from `persistence_result`;
- `error` information from failed task or failed step.

Frontend adds a `Trace` tab in Agent backstage. It renders the backend trace tree and shows each event type, status, duration, model/token data, retrieval query and hit count, tool call summaries, persistence summaries, and errors.

## Data Contract

`GenerationTask.trace`:

```json
{
  "trace_id": "generation-task-7",
  "root_span_id": "task-7",
  "events": [
    {
      "span_id": "task-7",
      "parent_span_id": null,
      "event_type": "task",
      "name": "chapter_generation",
      "status": "completed",
      "summary": "task completed",
      "duration_ms": 120,
      "metadata": {}
    }
  ]
}
```

Event fields:

- `span_id`: stable string id.
- `parent_span_id`: parent span id or `null`.
- `event_type`: `task`, `step`, `llm_call`, `retrieval`, `tool_call`, `persistence`, or `error`.
- `name`: readable event name.
- `status`: `pending`, `running`, `completed`, `failed`, or a domain-specific status.
- `summary`: compact UI text.
- `duration_ms`: integer or `null`.
- `metadata`: structured details for raw display.

## Error Handling

Trace building must not break generation APIs. If a snapshot has unexpected shape, that event is skipped or reduced to a safe summary. Failed tasks and failed steps still produce root and step events with error metadata.

## Testing

Backend tests verify:

- trace builder creates root and step spans;
- LLM usage becomes child `llm_call` events;
- RAG report becomes a `retrieval` event;
- tool calls become `tool_call` events;
- persistence result becomes a `persistence` event;
- generation API returns `trace`.

Frontend tests verify:

- Agent backstage has a `Trace` tab;
- trace events render model usage, RAG, tool calls, and persistence summaries.

## Future Extensions

Later stages can persist trace events in a table, expose a standalone trace API, add OpenTelemetry export, or connect Langfuse/LangSmith. This first stage keeps trace derived from already persisted generation state so it is low risk and useful immediately.
