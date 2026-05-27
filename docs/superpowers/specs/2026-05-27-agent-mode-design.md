# ScriptPilot AI Agent Mode Design

## Context

ScriptPilot currently uses a manual step-by-step workflow. The user enters a topic, then manually confirms or edits each stage: clarify, research, style, outline, script, and optionally content. This is valuable because users can control and edit outputs, but it requires repeated clicks.

The new AI Agent mode adds a chat-based workflow. The default site remains the traditional mode. Users can switch to AI Agent mode and interact with an Agent in one chat window. The Agent receives the topic, follows the workflow defined in `backend/agent/Agents.md`, runs each workflow step as a skill, returns each step result to the user, and pauses for confirmation or edits. If the user explicitly asks to run directly, the Agent continues automatically without pausing after each step.

The implementation should minimize changes to existing code. The Agent mode should be a new orchestration layer that reuses the existing backend stage functions instead of replacing the traditional flow.

## Goals

- Keep traditional mode as the default experience.
- Add an AI Agent mode that users can switch to from the frontend.
- Put the Agent implementation under `backend/agent/`.
- Store `Agents.md` and step-level `skill.md` files under `backend/agent/`.
- Treat each workflow step as a skill.
- Return each completed step result to the user in the chat.
- Pause by default after each skill so users can confirm, choose, or modify.
- Support an autopilot mode when the user explicitly asks to run directly.
- Reuse existing stage implementations as much as possible.

## Non-Goals

- No database or persistent chat history in the first version.
- No authentication or multi-user account model.
- No full rewrite of the existing manual workflow.
- No migration of the traditional UI to the Agent runtime.
- No complex branching beyond retry, continue, user edits, and autopilot.

## Recommended Architecture

Use `backend/agent/` as a backend orchestration boundary:

```text
backend/
  agent/
    Agents.md
    __init__.py
    api.py
    events.py
    runtime.py
    session.py
    skills/
      clarify.md
      research.md
      style.md
      outline.md
      script.md
      content.md
```

`backend/app.py` mounts the Agent router, but existing endpoints remain unchanged.

The Agent layer does not duplicate generation prompts. It reads workflow and skill definitions for orchestration metadata, then calls existing node functions and helpers:

- `backend.nodes.clarify.stream_clarify`
- `backend.nodes.research._search` and `_format_result`
- `backend.nodes.style.stream_style`
- `backend.graph.pipeline.run_stage_streaming`

This keeps the Agent mode as a chat-oriented controller over the existing generation system.

## Workflow Definition

`backend/agent/Agents.md` defines the workflow order and interaction rules:

```text
clarify -> research -> style -> outline -> script -> content
```

The `content` skill runs only when `CONTENT_ENABLED=true`. The `research` skill follows the existing `RESEARCH_ENABLED` configuration.

Each `backend/agent/skills/*.md` file defines:

- Skill purpose.
- Required inputs.
- Produced state fields.
- User-facing result summary.
- Pause behavior.
- Accepted user responses, such as confirm, edit, retry, skip, or continue.

The runtime treats these files as readable, local workflow documentation. The first implementation can hard-code the skill registry in Python while keeping the markdown files as the canonical workflow reference for future AI maintainers.

## Session Model

Use in-memory sessions for the first version.

Each session stores:

```python
{
    "id": "...",
    "topic": "...",
    "current_skill": "clarify",
    "autopilot": False,
    "state": {
        "topic": "",
        "direction": "",
        "direction_analysis": "",
        "style": "",
        "style_analysis": "",
        "research": "",
        "outline": "",
        "script": "",
        "content": "",
    },
    "pending": {
        "kind": "confirm" | "choice" | "edit" | None,
        "skill": "...",
        "options": [],
    },
}
```

Refreshing the page or restarting the backend can lose the Agent session. This matches the current MVP-style project and avoids adding storage before the interaction model is proven.

## Autopilot Rule

The default behavior is to pause after every completed skill.

If a user clearly asks to run directly, such as:

- "直接执行"
- "不用问我"
- "一直生成到最后"
- "自动继续"
- "run all"

then the session sets `autopilot=true`. While autopilot is enabled, the Agent continues to the next skill automatically after each skill completes. The Agent may still pause if it cannot proceed safely, for example when required input is missing and cannot be inferred.

Users can turn autopilot off by saying things like:

- "停一下"
- "每步问我"
- "先暂停"

## API Design

Add one streaming endpoint:

```http
POST /api/agent/chat
Content-Type: application/json

{
  "sessionId": "optional-session-id",
  "message": "帮我生成一个关于 AI 编程工具的视频脚本"
}
```

The response is SSE. The first request can omit `sessionId`; the backend creates one and returns it as an event.

### SSE Events

- `session`: `{"sessionId": "..."}`
- `message`: `{"role": "agent", "content": "..."}`
- `stage`: `{"stage": "outline", "status": "running"}`
- `thinking`: `{"stage": "outline", "token": "..."}`
- `token`: `{"stage": "outline", "token": "..."}`
- `option`: `{"id": "1", "title": "..."}`
- `results`: `{"results": [...]}`
- `artifact`: `{"stage": "outline", "content": "..."}`
- `paused`: `{"stage": "outline", "reason": "confirm_required", "prompt": "..."}`
- `done`: `{"state": {...}}`
- `error`: `{"message": "...", "retryable": true}`

The protocol intentionally mirrors the existing SSE events where possible so the frontend can reuse parsing logic.

## Skill Behavior

### clarify

Input: user topic.

Output:

- `direction_analysis`
- direction options

Default pause: ask the user to choose or write a custom direction.

Autopilot behavior: choose the first generated direction unless the user already gave a specific direction in the message.

### research

Input:

- `topic`
- `direction`

Output:

- research result cards
- selected research HTML or summary

Default pause: ask the user to confirm selected research material.

Autopilot behavior: use all returned research results. If research is disabled or no results are found, continue without research.

### style

Input:

- `topic`
- `direction`
- `direction_analysis`

Output:

- `style_analysis`
- style options

Default pause: ask the user to choose or write a custom style.

Autopilot behavior: choose the first generated style unless the user already gave a style preference.

### outline

Input:

- topic and direction
- style
- research
- direction and style analysis

Output: `outline`

Default pause: show the outline and ask the user to confirm or edit.

Autopilot behavior: continue with the generated outline.

### script

Input:

- outline
- style
- topic and direction

Output: `script`

Default pause: show the script and ask the user to confirm or edit.

Autopilot behavior: continue with the generated script.

### content

Input:

- script
- outline
- research
- style

Output: `content`

Runs only when `CONTENT_ENABLED=true`.

Default pause: show the generated article and mark the workflow complete.

Autopilot behavior: mark the workflow complete.

## Frontend Design

The default page remains traditional mode.

Add a mode switch near the main entry point:

- `传统模式`
- `AI Agent 模式`

AI Agent mode shows a chat workspace:

- Message list with user messages, Agent messages, stage progress, and generated artifacts.
- Chat input at the bottom.
- Action buttons on paused Agent messages:
  - `确认继续`
  - `修改后继续`
  - `重试这一步`
  - `直接执行到最后`
- For long markdown artifacts, reuse or extract the existing markdown editor/preview behavior from `MarkdownSplitPanel`.

The Agent UI should be independent from the existing sidebar step UI in the first version. This avoids coupling the new chat state to the manual flow state.

## Error Handling

If a skill fails, emit an `error` event and pause the session. The user can retry the current skill or provide a revised instruction.

The first version should support:

- Retry current skill.
- Continue to next skill when safe.
- Stop autopilot.
- Reset Agent session from the frontend.

LLM fallback behavior should stay inside the existing `stream_chain` utility.

## Testing Strategy

Backend tests should cover the Agent runtime without requiring real LLM calls:

- New message creates a session and starts with `clarify`.
- Default mode pauses after a skill completes.
- Autopilot mode continues after a skill completes.
- User confirmation advances to the next skill.
- User edits update state before continuing.
- `CONTENT_ENABLED=false` skips the content skill.
- Agent SSE events follow the expected event names and payload shapes.

Frontend verification:

- Traditional mode still opens by default.
- User can switch to AI Agent mode.
- Chat input sends messages to `/api/agent/chat`.
- Session id returned by the backend is retained for follow-up messages.
- Paused Agent messages show expected action buttons.
- Long artifacts render without breaking the layout.

If the project does not have frontend unit tests, use build verification and browser smoke testing for the first version.

## Implementation Notes

- Use test-driven development for the runtime behavior.
- Keep existing endpoints untouched except for importing and mounting the new Agent router.
- Keep the Python runtime small and explicit so future AI agents can understand the workflow from one directory.
- Prefer structured state transitions over prompt-only control.
- Make markdown workflow files concise and self-contained.

## Open Decisions Resolved

- Agent pauses by default after each skill.
- Explicit user intent can enable direct execution.
- The Agent implementation lives in `backend/agent/`.
- Traditional mode remains default.
- The first version uses in-memory sessions.
