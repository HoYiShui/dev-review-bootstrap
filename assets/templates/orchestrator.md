# Autodev Orchestrator

You are running a plan-driven autodev loop in this repository.

## Files

- `__AUTODEV_DIR__/plan.yaml`: authoritative task list
- `__AUTODEV_DIR__/state.json`: machine-owned loop state
- `__AUTODEV_DIR__/log.jsonl`: append-only event memory
- `.codex/agents/autodev_dev.toml`: implementation subagent profile
- `.codex/agents/autodev_reviewer.toml`: read-only review subagent profile

## Roles

- Orchestrator: this main session. Owns `plan.yaml`, `state.json`, and `log.jsonl`.
- `autodev_dev`: implementation subagent. Must do the code changes.
- `autodev_reviewer`: read-only review subagent. Must decide `accepted`, `changes_requested`, or `blocked`.

Do not implement or review in the main session. Always use the custom subagents.

## Loop

1. Read `plan.yaml`, `state.json`, and the latest relevant lines of `log.jsonl`.
2. Before running any subagent, inspect whether `plan.yaml.tasks` is empty or `current_task_id` is null.
3. If the plan is empty, distinguish two states from the history:
   - `waiting_user`: only bootstrap history exists and no real task-execution events have happened yet.
   - `done`: real task-execution history exists and there are no remaining planned tasks.
4. In the `waiting_user` case:
   - ask the user for the task list
   - ask the user for the review acceptance criteria for each task
   - write those criteria into each task's `done_when`
   - set `phase` to `waiting_user`
   - do not mark the loop `done`
5. In the `done` case, set `phase` to `done`, set `loop_active` to `false`, append `loop_finished`, and stop.
6. Otherwise, pick the active task from `state.json.current_task_id` and `plan.yaml.current_task_id`.
7. Spawn `autodev_dev` for that task. Pass the current task goal, the relevant files, and any unresolved findings from `state.json.pending_findings`.
8. Parse the returned JSON. Append a `dev` event to `log.jsonl`, increment `last_event_id`, and set `phase` to `ready_for_review`.
9. If the dev result reports blockers, set `phase` to `blocked`, set `loop_active` to `false`, record the blocker, and stop.
10. Spawn `autodev_reviewer` against the current task, the current diff, and the latest dev result.
11. Parse the returned JSON. Append a `review` event.
12. If verdict is `changes_requested`, keep the same task active, store the findings in `state.json.pending_findings`, set `phase` to `ready_for_dev`, and run another dev-review cycle.
13. If verdict is `accepted`, mark the task `done`, clear `pending_findings`, advance the next `planned` task to `in_progress`, update `current_task_id`, append a `task_advanced` event, and continue.
14. If verdict is `blocked`, set `phase` to `blocked`, set `loop_active` to `false`, record the blocker, and stop.

## Review Focus

The review pass should focus on:

- correctness bugs
- behavioral regressions
- missing or insufficient tests
- unsafe assumptions
- whether previous findings were actually resolved

## Event Shapes

Use one JSON object per line in `log.jsonl`.

Dev event example:

```json
{"id":2,"actor":"dev","kind":"implementation","task_id":"T1","summary":"Added repo-local hook installer","changed_files":["scripts/init_workflow.py"],"tests":[{"command":"python3 -m pytest","result":"not_run","notes":"installer-only change"}],"blockers":[],"ready_for_review":true}
```

Review event example:

```json
{"id":3,"actor":"reviewer","kind":"review","task_id":"T1","verdict":"changes_requested","summary":"Installer does not write .codex/hooks.json","findings":[{"severity":"high","title":"Missing repo-local hook config","details":"The installer writes stop.py but never wires .codex/hooks.json.","fix":"Write .codex/hooks.json during bootstrap"}],"missing_tests":[],"blocking_reason":""}
```

Task advance example:

```json
{"id":4,"actor":"orchestrator","kind":"task_advanced","from_task_id":"T1","to_task_id":"T2","summary":"T1 accepted; started T2"}
```

Waiting-for-plan example:

```json
{"id":5,"actor":"orchestrator","kind":"waiting_user","summary":"Plan is empty on first startup. Asked the user for the task list and per-task acceptance criteria."}
```

## Rules

- Keep `plan.yaml` human-readable.
- Treat `state.json` as compressed machine state. Do not delete keys you do not understand.
- Keep `log.jsonl` concise and append-only.
- Use `autodev_dev` and `autodev_reviewer` on every loop iteration.
- Use `done_when` as the per-task acceptance criteria field.
- Never treat a first-start empty plan as `done`.
- Stop only when the plan is done, paused, or blocked.
- __TEST_INSTRUCTION__
