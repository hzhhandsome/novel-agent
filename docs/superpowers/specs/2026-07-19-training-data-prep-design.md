# Training Data Prep Design

## Goal

Prepare clean future fine-tuning data without starting any training workflow.

## Scope

Export JSONL examples from accepted `GenerationRun` records:

- `context_to_chapter`: prompt package to accepted chapter text.
- `chapter_to_summary`: accepted chapter text to chapter summary.
- `chapter_to_audit`: prompt package and chapter text to audit result.

## Behavior

- Export only accepted runs by default.
- Include rejected runs only when explicitly requested.
- Each example includes task type, input, output, and metadata.
- Metadata includes project/chapter/run IDs and model snapshots, but no API keys.
- Service returns in-memory examples and can write JSONL to a file.
- CLI can export from the configured database to a path.

## Non-Goals

- Running fine-tuning jobs.
- Uploading data to a provider.
- User feedback diff samples, because full user rewrite/edit workflow is not active.
- Provider-specific fine-tuning format conversion.
