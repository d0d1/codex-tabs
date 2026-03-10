# Thread name storage investigation

## Goal

Check whether `codex-tabs` can display the Codex thread name created with `/rename thread` without scanning every transcript on every render.

## What was checked

- `threads.title` in `~/.codex/state_5.sqlite`
- the rest of the `threads` table columns
- other local state tables in `~/.codex/state_5.sqlite`
- `~/.codex/history.jsonl`
- the per-session JSONL transcript under `~/.codex/sessions/`

## Findings

- The only obvious user-facing thread-name field in the local state DB is `threads.title`.
- On this machine, `threads.title` still matches `first_user_message` even after using `/rename thread`.
- Other local tables did not expose an alternative persisted thread-name field.
- The session transcript JSONL contains structured events such as `session_meta`, `user_message`, `agent_message`, and tool calls, but no cheap standalone persisted field for the renamed thread name was identified.

## Conclusion

At the time of this investigation, Codex thread names created with `/rename thread` were not exposed in a cheap local field that `codex-tabs` could read directly.

## Decision

Do not add `thread name:` to the UI yet.

Parsing transcripts to recover rename commands was considered too costly for the normal display path.

## Related context

- Codex upstream clearly has a thread-naming concept.
- The missing piece is a reliable local field or documented storage location that `codex-tabs` can read cheaply.
