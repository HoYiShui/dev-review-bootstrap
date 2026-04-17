# Workflow Memory Design

This skill bootstraps a file-backed workflow memory model. The project files are intentionally split by lifetime and responsibility.

## Files

### `schedule.yaml`

- Purpose: task source of truth
- Writer: user or coordinator
- Readers: dev, reviewer
- Keep it small and structured

Recommended fields:

```yaml
current_task: T1
tasks:
  - id: T1
    title: Implement the workflow scaffold
    status: in_progress
    priority: 1
    exit_criteria:
      - dev_handoff_written
      - no_blocking_findings
```

Recommended statuses:

- `planned`
- `in_progress`
- `in_review`
- `changes_requested`
- `blocked`
- `done`

### `state/active_context.yaml`

- Purpose: current compressed state for the next dev turn
- Writer: hook memory refresh step
- Readers: dev, reviewer

Recommended fields:

```yaml
task_id: T1
goal: Finish the current task safely
current_constraints:
  - reviewer must stay read-only
next_step: Resolve the latest blocking finding
must_watch:
  - F1
```

### `state/dev_handoff.yaml`

- Purpose: one-turn handoff from the dev agent
- Writer: dev
- Readers: reviewer, user, hook

Recommended fields:

```yaml
turn_id: 20260417T180000
task_id: T1
summary: Added the project-local review scripts
changed_files:
  - path: .codex/workflow/hooks/run_reviewer.sh
tests:
  - name: not_run
    result: not_run
assumptions:
  - hooks are triggered by Stop
open_questions:
  - Should the review run on every turn?
review_focus:
  - hook recursion
```

### `state/open_findings.yaml`

- Purpose: unresolved reviewer findings across turns
- Writer: hook memory refresh step
- Readers: dev, reviewer

Recommended fields:

```yaml
findings:
  - id: F1
    task_id: T1
    severity: high
    title: Review hook can recurse without a guard
    status: open
    source_turn_id: 20260417T180000
    evidence: post_stop.sh re-invokes Codex without a recursion guard
    recommended_action: Add an env guard before spawning review
```

### `reviews/<turn_id>.json`

- Purpose: structured review artifact
- Writer: reviewer subprocess
- Readers: hook refresh step, user, dev when needed

The default scaffold uses structured JSON because it is easier to update memory files from a machine-readable artifact than from free-form Markdown.

## Hook Responsibility

The scaffolded hook logic intentionally does only three things automatically:

1. detect whether a fresh `dev_handoff.yaml` exists
2. run a structured reviewer subprocess
3. refresh `active_context.yaml` and `open_findings.yaml`

It does not try to fully rewrite `schedule.yaml`, because that file is both user-facing and task-authoritative.

## Global Dispatcher Model

The skill can optionally install a user-level `Stop` dispatcher in `~/.codex/hooks.json`.

That dispatcher is safe to keep global because it only forwards into a repository if the repository contains:

```text
.codex/workflow/hooks/post_stop.sh
```

This avoids hard-coding one repository path into the global hook file.
