# Novel Agent V1 Requirements Analysis

## 1. Product Positioning

Novel Agent V1 is an automation-first long-form fiction writing system. Its goal is not only to provide writing assistance, but to let the agent automatically plan, generate, compress, update memory, manage foreshadowing, and review drafts while allowing the author to intervene at any time.

The author can provide inspiration, direction, character changes, plot turns, style preferences, or manual prose at any point. The agent must incorporate these inputs into the project state and continue automation from the updated direction.

V1 should be designed as a web application first, with a path to desktop packaging later through Tauri. The agent engine should remain independent from the UI so it can be reused by the desktop shell.

Recommended stack:

- Frontend: React + Vite + TypeScript
- Desktop shell later: Tauri
- Agent backend: Python + FastAPI + LangGraph
- Local persistence: SQLite plus local project files
- Model access: provider adapter layer for cloud and local models

## 2. Core Product Principle

The system should automate fiction production, but not silently corrupt the novel canon.

Automation should be the default for routine generation, summarization, draft expansion, chapter planning, style application, and non-critical memory updates. Human confirmation is required for changes that alter canon, locked constraints, major character motivation, main plot direction, or important foreshadowing recovery.

The default operating mode for V1 is "key-change confirmation":

- Routine work runs automatically.
- Major canon changes pause and ask the author to confirm.
- The author can switch to full automation, per-chapter confirmation, or manual assistance mode.

## 3. Primary User Experience

The first screen is a writing cockpit, not a landing page.

### 3.1 Layout

The UI has four main regions:

- Left sidebar: novel structure, volumes, chapters, fragments, and generation status.
- Center editor: current chapter content and author takeover area.
- Right sliding module panel: configurable modules such as world constraints, character cards, style, positioning, foreshadowing, main plot, and inspiration input.
- Bottom agent workspace: shows the agent's meaningful creative work, not generic system logs.

### 3.2 Left Sidebar

The left sidebar supports:

- Volume and chapter tree.
- Draft, generated, reviewed, accepted, and locked status indicators.
- Chapter creation, regeneration, and ordering.
- Unassigned fragments or inspiration notes.
- Per-chapter automation status.

### 3.3 Center Editor

The editor supports:

- Reading and editing chapter prose.
- Manual author writing.
- Selecting text for local rewrite, expansion, compression, continuation, or review.
- Showing generated candidates before insertion.
- Accepting, rejecting, editing, or regenerating output.
- Inserting author inspiration into the current scene or future plan.

### 3.4 Right Module Panel

The right panel is modular and can become long, so modules must be collapsible, reorderable, and removable.

Initial modules:

- Novel positioning: genre, audience, length, pacing, core appeal, forbidden directions.
- Style configuration: prose style, tone, narrative perspective, forbidden expressions, pacing.
- World constraints: hard rules, soft rules, location rules, magic or technology constraints, social structure.
- Main plot: current arc, long-term direction, current chapter goal, forbidden spoilers.
- Character cards: character list and period cards.
- Inspiration input: author can inject plot turns, character changes, scenes, lines, or constraints.
- Foreshadowing and promise ledger: active clues, reader promises, emotional debts, relationship debts.
- Automation settings: full automation, per-chapter confirmation, key-change confirmation, manual assistance.

## 4. Automation Workflow

V1 should support an automatic loop from project setup to chapter generation.

### 4.1 Project Initialization

The agent can generate or accept manual input for:

- Novel title and working title.
- Genre and subgenre.
- Reader positioning.
- Target length and chapter size.
- Core appeal.
- Main conflict.
- World premise.
- Protagonist and major characters.
- Long-term main plot.
- Style defaults.

The author can lock any generated item. Locked items cannot be overwritten by later automation without explicit confirmation.

### 4.2 Chapter Generation Loop

For each chapter, the agent performs:

1. Build chapter target: purpose, emotional beat, plot advancement, viewpoint, end hook.
2. Build generation prompt package: current chapter target, relevant character period cards, world constraints, style, prior summaries, active foreshadowing, forbidden spoilers.
3. Generate chapter outline or scene beats.
4. Generate prose.
5. Review prose.
6. Propose revisions.
7. Accept, edit, or regenerate.
8. Update memory after acceptance.

The author can interrupt at any step with new inspiration or manual writing. The agent then recalculates affected plot, character, memory, and foreshadowing state.

### 4.3 Automation Modes

V1 supports four modes:

- Full automation: the agent keeps generating chapters and pauses only on severe conflicts.
- Per-chapter confirmation: each chapter requires author confirmation before continuing.
- Key-change confirmation: routine work is automatic, but canon-impacting changes require confirmation.
- Assistance mode: the author writes manually and uses the agent for local generation, review, and organization.

The default is key-change confirmation.

## 5. Agent Creative Workspace

The bottom panel should show where the agent is doing useful creative work. It should avoid low-value logs such as raw API status or generic progress messages.

Required bottom-panel sections:

- Chapter compression: shows when context is near limit and what is being compressed.
- Memory promotion: shows which events are being promoted to character memory, world facts, plot state, or foreshadowing.
- Character prompt generation: shows the role-specific prompt used for this chapter or scene.
- Generation prompt package: shows the actual creative constraints used for the next generation.
- Foreshadowing ledger updates: shows clues created, advanced, delayed, recovered, or blocked.
- Review findings: shows character consistency, world conflict, pacing, spoiler leakage, repetition, and plot drift.
- Canon change gates: shows what requires author approval before entering official memory.

The bottom panel must expose intermediate artifacts that the author can accept, edit, reject, or regenerate.

## 6. Long-Form Memory System

Long-form writing requires memory beyond the current context window.

### 6.1 Chapter Compression

When context approaches a configured threshold, the agent automatically compresses earlier chapters.

Compression output includes:

- Plot facts.
- Character changes.
- Relationship changes.
- World facts introduced.
- Active foreshadowing.
- Reader promises.
- Unresolved conflicts.
- Forbidden contradictions.

The author can inspect, edit, accept, or regenerate compression output before it enters long-term memory.

### 6.2 Memory Promotion

Generated or manually written content can be promoted into:

- Chapter summary.
- Character period memory.
- World fact.
- Main plot state.
- Foreshadowing ledger.
- Style note.
- Forbidden direction.

Promotion should not be fully silent for important facts. V1 should automatically suggest promotions and require confirmation for canon-impacting changes.

### 6.3 Draft and Canon Isolation

The system must distinguish:

- Accepted canon prose.
- Author plan.
- Candidate draft.
- Rejected draft.
- Generated suggestion.
- Locked rule.
- Hidden spoiler.

Only accepted canon and confirmed memory should influence future generation by default. Candidate and rejected material must not pollute memory.

## 7. Character Period Cards

Characters are not represented by a single static card. Each important character has period cards.

Each period card includes:

- Period name.
- Active chapters or arc range.
- Public identity.
- Private motivation.
- Current belief.
- Emotional state.
- Relationships.
- Secrets.
- Key memories.
- Speaking style.
- Behavioral constraints.
- Forbidden actions.
- Current chapter prompt.

The agent can generate new period cards when plot progression changes a character. Core motivation changes require author confirmation.

Example flow:

1. Character appears in a new arc.
2. Agent detects changed motivation or memory.
3. Agent proposes a new period card.
4. Author accepts, edits, or rejects.
5. Accepted card becomes available for later generation.

## 8. Foreshadowing and Promise Ledger

The system should track more than traditional foreshadowing.

Ledger item types:

- Plot clue.
- Mystery.
- Reader promise.
- Emotional debt.
- Relationship debt.
- Power or ability setup.
- World rule setup.
- Character secret.

Each ledger item includes:

- Source chapter or scene.
- Current status: planted, advanced, delayed, ready to recover, recovered, abandoned.
- Allowed visibility.
- Spoiler risk.
- Planned recovery range.
- Related characters.
- Related world facts.
- Notes for generation.

The agent should automatically suggest new ledger items when generated or accepted text creates a reader expectation. The agent should warn when generation risks revealing a clue too early or forgetting a long-running promise.

## 9. Review System

The review system runs before generated prose becomes accepted chapter content.

Review dimensions:

- Character consistency.
- Motivation plausibility.
- World constraint conflict.
- Main plot alignment.
- Foreshadowing leakage.
- Foreshadowing neglect.
- Pacing and chapter hook.
- Repetition.
- Style drift.
- Continuity conflict.

The review system should return actionable findings, not generic scores.

Each finding includes:

- Problem type.
- Location or affected passage.
- Why it matters.
- Suggested fix.
- Whether it blocks automatic acceptance.

V1 should not automatically rewrite accepted prose without user approval.

## 10. Author Intervention

The author can intervene at any time.

Supported intervention types:

- Add inspiration.
- Change plot direction.
- Lock or unlock setting.
- Add or edit character card.
- Add hidden spoiler.
- Rewrite selected text.
- Manually write a scene.
- Reject generated direction.
- Force regeneration.
- Change automation mode.

When an intervention affects future generation, the agent should recalculate:

- Main plot direction.
- Current and future chapter targets.
- Character cards.
- Foreshadowing ledger.
- World constraints.
- Prompt package.

The system should show the impact scope before applying major changes.

## 11. Data Objects

V1 should persist these core objects:

- Project.
- Volume.
- Chapter.
- Scene or fragment.
- Novel positioning.
- Style profile.
- World rule.
- Character.
- Character period card.
- Chapter summary.
- Memory item.
- Foreshadowing or promise item.
- Inspiration note.
- Generation run.
- Review finding.
- Automation setting.
- Lock or confirmation gate.

Generation runs should record:

- Task type.
- Model and parameters.
- Input context references.
- Prompt package.
- Output.
- Review result.
- User decision.
- Timestamp.

This history is required for rollback and debugging generation quality.

## 12. MVP Scope

V1 must include:

- Project creation.
- Four-region writing cockpit.
- Chapter tree and editor.
- Right-side configurable modules.
- Automatic project setup generation.
- Automatic chapter generation loop.
- Author inspiration injection.
- Character period cards.
- Chapter compression.
- Memory promotion.
- Prompt package preview.
- Foreshadowing and promise ledger.
- Review findings.
- Automation mode selection.
- Local persistence.
- Generation history and rollback.

V1 can defer:

- Multi-user collaboration.
- Cloud sync.
- Marketplace templates.
- Full docx export polish.
- Rich typography publishing layout.
- Advanced vector database tuning.
- Multi-agent UI with separate named agents.
- Mobile layout.
- Plugin system.

## 13. Technical Architecture

The architecture should separate UI, API, agent workflow, and persistence.

### 13.1 Frontend

React + TypeScript provides the cockpit UI:

- Chapter tree.
- Editor.
- Right module panel.
- Bottom agent workspace.
- Generation controls.
- Review and confirmation dialogs.

The frontend should treat the backend as the source of truth for project state.

### 13.2 Backend API

FastAPI exposes:

- Project CRUD.
- Chapter CRUD.
- Module state.
- Generation task start and status.
- Review result retrieval.
- Confirmation gates.
- History and rollback.

Long-running generation should be represented as tasks with durable state, not one blocking request.

### 13.3 Agent Workflow

LangGraph models the automation workflow:

- Project setup graph.
- Chapter generation graph.
- Compression graph.
- Memory promotion graph.
- Review graph.
- Intervention recalculation graph.

Each node should produce structured intermediate artifacts that can be shown in the bottom agent workspace.

### 13.4 Persistence

SQLite stores structured project state. Large generated text can be stored in SQLite or project-local files, with references in the database.

The persistence layer must protect draft/canon separation and support rollback.

## 14. Open Design Decisions

The following decisions should be resolved before implementation planning:

- Editor engine: plain textarea first, TipTap, or Monaco-style editor.
- Local model support in V1 or cloud-provider-only first.
- Whether full automation can generate multiple chapters in one run in V1.
- Exact confirmation gates for memory promotion.
- Storage format for project export.
- Whether semantic retrieval is needed in V1 or structured memory is enough.

Recommended defaults:

- Use a pragmatic rich text or markdown editor, not a complex publishing editor.
- Cloud-provider adapter first, local model adapter interface reserved.
- Allow multi-chapter automation only after single-chapter loop is stable.
- Require confirmation for canon-changing memory promotion.
- Use SQLite plus markdown export.
- Start with structured retrieval; add vector retrieval after memory objects stabilize.

## 15. Success Criteria

V1 is successful if a user can:

- Create a new novel from a short idea.
- Let the agent generate positioning, world, main plot, and characters.
- Run automatic chapter generation.
- Inject a new inspiration mid-process and see the agent recalculate affected state.
- Generate or update character period cards.
- Continue writing after context grows by using chapter compression.
- Track foreshadowing and reader promises.
- Review generated prose before accepting it.
- Recover from bad generations through history and rollback.
- Maintain clear separation between canon, plans, drafts, rejected outputs, and locked rules.

The core promise is: the agent can continue a long novel automatically while preserving the author's ability to direct, correct, and protect the story's canon.
