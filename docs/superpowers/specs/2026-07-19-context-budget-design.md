# Context Budget Design

## Goal

Add a first P0 context budget system to prevent `load_context` from loading all summaries, memories, foreshadowing, and inspirations into the prompt as projects grow.

## Scope

This design covers a rule-based budget in `load_context`:

- Character or token approximation using character counts.
- Fixed sections for project positioning, worldview, main plot, character periods, active foreshadowing, and world rules.
- Bounded sections for chapter summaries, story events, and author inspirations.
- A `context_budget` report in `context_package` with included, omitted, and usage information.
- Agent backstage context display for budget usage and omitted content.

This design does not add embeddings, vector search, re-ranking, model tokenizers, or user-configurable budget UI. RAG will consume this budget mechanism later.

## Budget Policy

Use deterministic character budgets for the first implementation:

- Total budget: 6000 characters.
- Core project settings: fixed and always included.
- Character periods: fixed and always included.
- Active foreshadowing: fixed and always included until section budget is reached.
- Active world rules: fixed and always included until section budget is reached.
- Recent chapter summaries: newest accepted summaries first.
- Story events: newest events first.
- Inspirations: newest unapplied inspirations first.

When a bounded section exceeds its budget, omit the rest and record them in `context_budget.omitted`.

## Context Package Shape

`context_package` will keep current keys and add:

```json
{
  "context_budget": {
    "total_budget": 6000,
    "used": 4200,
    "sections": [
      {
        "name": "chapter_summaries",
        "budget": 1600,
        "used": 900,
        "included_count": 5,
        "omitted_count": 8
      }
    ],
    "omitted": {
      "chapter_summaries": ["第 1 章：..."],
      "story_events": ["第 2 章：..."],
      "inspirations": ["..."]
    }
  }
}
```

The context string used by prompt building must be based on the included items only.

## Display

Agent backstage context tab shows:

- Context budget usage.
- Included/omitted counts per section.
- Omitted content preview.

## Tests

Backend tests:

- Build a project with many accepted chapter summaries and events.
- Generate a chapter.
- Assert `load_context.output_snapshot.context_package.context_budget` exists.
- Assert included summaries are bounded and omitted summaries are recorded.
- Assert prompt package does not include omitted old summary text.

Frontend tests:

- Agent context tab displays budget usage and omitted content summary when present.
