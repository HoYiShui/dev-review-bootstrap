## Autodev Loop

- If `__AUTODEV_DIR__/state.json` has `"loop_active": true`, act as the repository orchestrator.
- Read `__AUTODEV_DIR__/ORCHESTRATOR.md`, `__AUTODEV_DIR__/plan.yaml`, `__AUTODEV_DIR__/state.json`, and the latest lines of `__AUTODEV_DIR__/log.jsonl` before resuming.
- Use the project-scoped custom agents `autodev_dev` and `autodev_reviewer`. Do not implement or review directly in the main session.
- Treat `__AUTODEV_DIR__/plan.yaml` as the task source of truth.
- Treat `__AUTODEV_DIR__/state.json` as machine-owned loop state.
- Append concise JSON objects to `__AUTODEV_DIR__/log.jsonl` for each dev pass, review pass, and task transition.
- Do not stop while the loop is still actionable. Stop only when the plan is done, paused, or blocked on external input.
