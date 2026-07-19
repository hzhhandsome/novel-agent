# Author Input Review Design

## Goal

Add first-stage AI review for user-entered creative inputs before they affect project state.

## Scope

P0 first stage covers:

- Project idea before project creation.
- Author inspiration before insertion into project memory.

Body rewrite/edit review is explicitly out of this stage because the first version currently does not support user modification workflows for accepted chapters.

## Behavior

- Backend exposes an input-review API returning `pass`, `warning`, or `block`.
- Review result includes reason and suggestions.
- Frontend calls review before project creation and before adding inspiration.
- `block` stops the write and shows the reason.
- `pass` and `warning` continue the existing write path and display the latest review result.
- Review does not auto-rewrite user input.

## Review Dimensions

- Conflict with worldview or project positioning.
- Character motivation damage.
- Contradiction with accepted summaries.
- Foreshadowing leakage.
- Too vague to guide generation.

## Provider

Add `review_user_input` to `ModelProvider`. Mock provider uses deterministic heuristics for tests. DeepSeek provider asks for strict JSON.

## Non-Goals

- Human confirmation modal for warning.
- Accepted-chapter rewrite or body-edit review.
- Automatic input rewriting.
- Persisting review history.
