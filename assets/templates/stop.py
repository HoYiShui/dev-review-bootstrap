#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


NON_ACTIONABLE_PHASES = {"idle", "paused", "blocked", "done", "waiting_user"}
DEFAULT_REASON = (
    "Autodev loop is still active. Read __AUTODEV_DIR__/ORCHESTRATOR.md, "
    "__AUTODEV_DIR__/plan.yaml, __AUTODEV_DIR__/state.json, and "
    "__AUTODEV_DIR__/log.jsonl. Continue as the orchestrator. Use the custom "
    "subagents autodev_dev and autodev_reviewer. If the current task is unfinished, "
    "run another dev-review cycle. If review accepts, advance the next planned task. "
    "Stop only when the plan is done, paused, or blocked."
)


def load_hook_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def load_state(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def should_continue(state: dict) -> bool:
    if not state.get("loop_active"):
        return False
    if not state.get("auto_continue", True):
        return False
    phase = state.get("phase", "")
    if phase in NON_ACTIONABLE_PHASES:
        return False
    current_task_id = state.get("current_task_id")
    if current_task_id in (None, "") and phase not in {"advancing"}:
        return False
    return True


def main() -> int:
    _payload = load_hook_payload()
    repo_root = Path(__file__).resolve().parents[3]
    state_path = repo_root / "__AUTODEV_DIR__" / "state.json"
    state = load_state(state_path)

    if not should_continue(state):
        return 0

    reason = state.get("continue_prompt") or DEFAULT_REASON
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
