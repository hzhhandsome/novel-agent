# Structured Memory Design

## Goal

Implement the first P0 structured memory slice so the project no longer treats chapter summaries as the only long-term memory. The slice must add stable character period state, event timeline entries, and world rule records that are visible in context and the right-side module panel.

## Scope

This design covers:

- Character period fields on existing character cards.
- Project-level story events.
- Project-level world rules.
- Loading these records into `load_context`.
- Persisting basic official memory when a chapter candidate is accepted.
- Displaying the new memory in project APIs, TypeScript types, the module panel, and Agent context view.

This design does not add vector search, recall metrics, manual per-memory approval, or a separate memory editing UI. Those are separate P0/P1 items in the roadmap.

## Data Model

Extend `Character`:

- `period_stage`: current character period/stage name.
- `period_summary`: short explanation of the character's current period state.
- `period_source_chapter_id`: source chapter that last changed the period state.

Add `StoryEvent`:

- `project_id`
- `source_chapter_id`
- `title`
- `summary`
- `characters`
- `location`
- `consequence`

Add `WorldRule`:

- `project_id`
- `source_chapter_id`
- `rule`
- `limitation`
- `exception`
- `status`

## Flow

Project creation initializes:

- Character period fields from the generated character seed.
- One baseline world rule from `project.worldview`.

`load_context` loads:

- Character period fields with current goals and memories.
- Existing story events.
- Existing world rules.

Chapter acceptance persists official memory:

- A story event from the accepted chapter summary.
- Character period summary updates from `judge_character_period`.
- A chapter-scoped world rule note when the chapter summary introduces a new official constraint.

The candidate save node still does not mutate formal memory. Formal memory updates only happen through the accept path, including full-auto acceptance.

## Display

Right-side module panel:

- Character cards show current period/stage.
- Add Event Timeline section.
- Add World Rules section.

Agent backstage context tab:

- Current character period cards include period stage and summary.
- Add story events and world rules cards.

## Testing

Backend tests must prove:

- Project creation returns character period fields and baseline world rules.
- Accepted chapters create story event records and update character period summary.
- `load_context` includes character period, event timeline, and world rules.

Frontend tests must prove:

- Module panel displays character period, event timeline, and world rules.
- Agent context tab displays structured memory from real context package or project fallback.
