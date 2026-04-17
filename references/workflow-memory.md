# Autodev Memory Design

This skill bootstraps a small memory model for an orchestrator-style autodev loop. The files are intentionally split by responsibility:

- `plan.yaml`: stable task plan
- `state.json`: compressed machine-owned runtime state
- `log.jsonl`: append-only dev/review history
- `.codex/agents/*.toml`: hard role separation for `dev` and `reviewer`

## `plan.yaml`

- Purpose: authoritative task list
- Writers: user or orchestrator
- Readers: orchestrator, dev pass, review pass
- Keep it human-readable and small

Recommended shape:

```yaml
version: 1
current_task_id: T1
tasks:
  - id: T1
    title: Implement the workflow scaffold
    status: in_progress
    priority: 1
    done_when:
      - implementation complete
      - reviewer accepts
```

Recommended statuses:

- `planned`
- `in_progress`
- `blocked`
- `done`

## `state.json`

- Purpose: machine-owned loop cursor and compressed status
- Writers: orchestrator, optional Codex `Stop` hook
- Readers: orchestrator, optional Codex `Stop` hook
- Keep it stable; avoid deleting keys casually

Recommended shape:

```json
{
  "version": 1,
  "subagents_required": true,
  "dev_agent_name": "autodev_dev",
  "reviewer_agent_name": "autodev_reviewer",
  "loop_active": true,
  "auto_continue": true,
  "phase": "ready_for_dev",
  "current_task_id": "T1",
  "iteration": 0,
  "review_round": 0,
  "last_event_id": 3,
  "last_actor": "reviewer",
  "last_verdict": "changes_requested",
  "pending_findings": [
    {
      "severity": "high",
      "title": "Installer does not write .codex/hooks.json",
      "fix": "Add repo-local hook installation"
    }
  ],
  "blocked_reason": "",
  "continue_prompt": "Autodev loop is still active. Read the workflow files and continue."
}
```

Suggested phases:

- `idle`
- `ready_for_dev`
- `ready_for_review`
- `fixing`
- `blocked`
- `done`
- `paused`

## `log.jsonl`

- Purpose: durable event memory across dev and review passes
- Writer: orchestrator
- Readers: orchestrator, user
- One JSON object per line

Recommended event types:

- `bootstrap`
- `implementation`
- `review`
- `task_advanced`
- `blocked`
- `loop_finished`

Example lines:

```json
{"id":1,"actor":"bootstrap","kind":"bootstrap","task_id":"T1","summary":"Installed autodev scaffold with 3 tasks"}
{"id":2,"actor":"dev","kind":"implementation","task_id":"T1","summary":"Added repo-local hook installer","changed_files":["scripts/init_workflow.py"],"tests":[{"command":"python3 -m pytest","result":"not_run","notes":"installer-only change"}],"blockers":[],"ready_for_review":true}
{"id":3,"actor":"reviewer","kind":"review","task_id":"T1","verdict":"changes_requested","summary":"Missing hook target file","findings":[{"severity":"high","title":"stop.py is not written","details":"The hook config is missing.","fix":"Write the hook target into .codex/autodev/hooks/stop.py"}],"missing_tests":[],"blocking_reason":""}
```

## Why This Split

- `plan.yaml` stays readable and user-editable.
- `state.json` stays small and machine-friendly for automatic continuation.
- `log.jsonl` preserves the detailed trail without forcing the orchestrator to parse a huge prose log.
- `.codex/agents/autodev_dev.toml` and `.codex/agents/autodev_reviewer.toml` provide hard prompt isolation instead of relying on soft role prompts.

## Custom Agents

The scaffold installs two project-scoped Codex custom agents:

- `.codex/agents/autodev_dev.toml`
- `.codex/agents/autodev_reviewer.toml`

The orchestrator should always use these agents for implementation and review. The main session should not directly implement or review. This keeps the role boundary stable across long loops.

## Codex `Stop` Hook

For Codex, the scaffold can install a repo-local `.codex/hooks.json` entry that points at:

```text
.codex/autodev/hooks/stop.py
```

That hook should be simple:

1. read `state.json`
2. if the loop is still active, emit `{"decision":"block","reason":"..."}` to keep the orchestrator running
3. otherwise do nothing and allow the agent to stop

The hook does not run dev or review itself. It only prevents premature termination while the loop is still actionable.
