## Autodev Loop

- If `__AUTODEV_DIR__/state.json` has `"loop_active": true`, act as the repository orchestrator.
- Read `__AUTODEV_DIR__/ORCHESTRATOR.md`, `__AUTODEV_DIR__/plan.yaml`, `__AUTODEV_DIR__/state.json`, and the latest lines of `__AUTODEV_DIR__/log.jsonl` before resuming.
- Use the project-scoped custom agents `autodev_dev` and `autodev_reviewer`. Do not implement or review directly in the main session.
- Treat `__AUTODEV_DIR__/plan.yaml` as the task source of truth.
- Treat `__AUTODEV_DIR__/state.json` as machine-owned loop state.
- If `plan.yaml` has no tasks or `current_task_id` is null, do not immediately mark the loop done.
- Distinguish two cases from simple history:
  - First startup / missing plan definition: if the log has no real task-execution history beyond bootstrap, ask the user for the task list first.
  - Actual completion: only treat an empty or exhausted plan as `done` when the history shows that tasks existed and have already been completed.
- In the first-startup case, ask the user for:
  - the task list
  - the review acceptance criteria for each task
- Write those acceptance criteria into each task's `done_when` field before starting the dev-review loop.
- In the first-startup case, use `waiting_user` rather than `done`.
- Append concise JSON objects to `__AUTODEV_DIR__/log.jsonl` for each dev pass, review pass, and task transition.
- Do not stop while the loop is still actionable. Stop only when the plan is done, paused, or blocked on external input.
