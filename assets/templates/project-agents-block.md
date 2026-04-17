## Dev/Review Workflow

- Treat `__WORKFLOW_DIR__/schedule.yaml` as the task source of truth.
- Before ending a substantial implementation turn, update `__WORKFLOW_DIR__/state/dev_handoff.yaml`.
- Read `__WORKFLOW_DIR__/state/active_context.yaml` before resuming work on the current task.
- Treat `__WORKFLOW_DIR__/state/open_findings.yaml` as the unresolved review queue.
- Do not use `reviews/` as the default prompt context. Read the latest artifact only when needed.
- Keep the workflow files concise and structured.
