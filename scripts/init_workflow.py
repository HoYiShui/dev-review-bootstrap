#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"
BLOCK_START = "<!-- BEGIN MANAGED BLOCK: dev-review-bootstrap -->"
BLOCK_END = "<!-- END MANAGED BLOCK: dev-review-bootstrap -->"


def render_template(name: str, replacements: dict[str, str]) -> str:
    text = (TEMPLATE_DIR / name).read_text()
    for key, value in replacements.items():
        text = text.replace(f"__{key}__", value)
    return text


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def upsert_managed_block(path: Path, block_body: str) -> None:
    managed = f"{BLOCK_START}\n{block_body.rstrip()}\n{BLOCK_END}\n"
    if not path.exists():
        path.write_text(managed)
        return

    existing = path.read_text()
    if BLOCK_START in existing and BLOCK_END in existing:
        start = existing.index(BLOCK_START)
        end = existing.index(BLOCK_END) + len(BLOCK_END)
        updated = existing[:start] + managed + existing[end:]
    else:
        joiner = "" if existing.endswith("\n") or not existing else "\n\n"
        updated = existing + joiner + managed
    path.write_text(updated)


def load_task_list(path: Path) -> list[str]:
    tasks = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        tasks.append(line)
    return tasks


def build_plan(mode: str, task_title: str, task_list: list[str]) -> str:
    lines = ["version: 1"]

    if mode == "empty":
        lines.extend(["current_task_id: null", "tasks: []"])
        return "\n".join(lines) + "\n"

    if mode == "single-task":
        task_list = [task_title or "Initial task"]

    if not task_list:
        raise SystemExit("task-list mode requires at least one task")

    lines.extend(["current_task_id: T1", "tasks:"])
    for index, title in enumerate(task_list, start=1):
        task_id = f"T{index}"
        status = "in_progress" if index == 1 else "planned"
        lines.extend(
            [
                f"  - id: {task_id}",
                f"    title: {json.dumps(title, ensure_ascii=False)}",
                f"    status: {status}",
                f"    priority: {index}",
                "    done_when:",
                "      - implementation complete",
                "      - reviewer accepts",
            ]
        )
    return "\n".join(lines) + "\n"


def build_state(
    mode: str,
    test_command: str,
    autodev_dir: str,
    install_stop_hook: bool,
) -> str:
    has_tasks = mode != "empty"
    current_task_id = "T1" if has_tasks else None
    state = {
        "version": 1,
        "subagents_required": True,
        "dev_agent_name": "autodev_dev",
        "reviewer_agent_name": "autodev_reviewer",
        "loop_active": has_tasks,
        "auto_continue": has_tasks and install_stop_hook,
        "phase": "ready_for_dev" if has_tasks else "idle",
        "current_task_id": current_task_id,
        "iteration": 0,
        "review_round": 0,
        "last_event_id": 1,
        "last_actor": "bootstrap",
        "last_verdict": "none",
        "pending_findings": [],
        "blocked_reason": "",
        "last_summary": "Bootstrap scaffold installed",
        "test_command": test_command,
        "continue_prompt": (
            f"Autodev loop is still active. Read {autodev_dir}/ORCHESTRATOR.md, "
            f"{autodev_dir}/plan.yaml, {autodev_dir}/state.json, and "
            f"{autodev_dir}/log.jsonl. Then continue as the orchestrator. Use the "
            "custom subagents named autodev_dev and autodev_reviewer. If the current "
            "task is unfinished, run another dev-review cycle. If review accepts, "
            "advance the next planned task. Stop only when the plan is done, paused, "
            "or blocked on external input."
        ),
    }
    return json.dumps(state, indent=2, ensure_ascii=False) + "\n"


def build_log(mode: str, task_title: str, task_list: list[str], test_command: str) -> str:
    if mode == "single-task":
        task_count = 1
        summary = f"Installed autodev scaffold with 1 task: {task_title or 'Initial task'}"
        task_id = "T1"
    elif mode == "task-list":
        task_count = len(task_list)
        summary = f"Installed autodev scaffold with {task_count} tasks"
        task_id = "T1"
    else:
        task_count = 0
        summary = "Installed autodev scaffold with an empty plan"
        task_id = None

    event = {
        "id": 1,
        "actor": "bootstrap",
        "kind": "bootstrap",
        "task_id": task_id,
        "summary": summary,
        "plan_mode": mode,
        "task_count": task_count,
        "test_command": test_command or None,
    }
    return json.dumps(event, ensure_ascii=False) + "\n"


def build_test_instruction(test_command: str) -> str:
    if test_command:
        return (
            f'Default project test command: `{test_command}`. Run it when the task '
            "scope justifies it, or record clearly why it was skipped."
        )
    return (
        "No default project test command is configured. Choose the smallest relevant "
        "verification for each task and record it in `log.jsonl`."
    )


def install_repo_stop_hook(project_root: Path, autodev_dir: str) -> None:
    hooks_path = project_root / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    if hooks_path.exists():
        data = json.loads(hooks_path.read_text())
    else:
        data = {"hooks": {}}

    hooks = data.setdefault("hooks", {})
    stop_rules = hooks.setdefault("Stop", [])
    command = f'python3 "$(git rev-parse --show-toplevel)/{autodev_dir}/hooks/stop.py"'

    for rule in stop_rules:
        for hook in rule.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command") == command:
                hooks_path.write_text(json.dumps(data, indent=2) + "\n")
                return

    stop_rules.append(
        {
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "statusMessage": "Checking autodev continuation",
                }
            ]
        }
    )
    hooks_path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--autodev-dir", default=".codex/autodev")
    parser.add_argument(
        "--plan-mode",
        choices=["empty", "single-task", "task-list"],
        default="empty",
    )
    parser.add_argument("--task-title", default="")
    parser.add_argument("--task-list-file")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--install-stop-hook", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    autodev_dir = project_root / args.autodev_dir
    hooks_dir = autodev_dir / "hooks"
    codex_agents_dir = project_root / ".codex" / "agents"

    task_list = []
    if args.task_list_file:
        task_list = load_task_list(Path(args.task_list_file).resolve())

    plan_text = build_plan(args.plan_mode, args.task_title, task_list)
    state_text = build_state(
        args.plan_mode,
        args.test_command,
        args.autodev_dir,
        args.install_stop_hook,
    )
    log_text = build_log(args.plan_mode, args.task_title, task_list, args.test_command)

    replacements = {
        "AUTODEV_DIR": args.autodev_dir,
        "TEST_INSTRUCTION": build_test_instruction(args.test_command),
    }

    autodev_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    codex_agents_dir.mkdir(parents=True, exist_ok=True)
    write_text(autodev_dir / "plan.yaml", plan_text, overwrite=args.force)
    write_text(autodev_dir / "state.json", state_text, overwrite=args.force)
    write_text(autodev_dir / "log.jsonl", log_text, overwrite=args.force)
    write_text(
        autodev_dir / "ORCHESTRATOR.md",
        render_template("orchestrator.md", replacements),
        overwrite=args.force,
    )
    write_text(hooks_dir / "stop.py", render_template("stop.py", replacements), overwrite=args.force)
    write_text(
        codex_agents_dir / "autodev_dev.toml",
        render_template("dev-agent.toml", replacements),
        overwrite=args.force,
    )
    write_text(
        codex_agents_dir / "autodev_reviewer.toml",
        render_template("reviewer-agent.toml", replacements),
        overwrite=args.force,
    )

    (hooks_dir / "stop.py").chmod(0o755)

    agents_block = render_template("project-agents-block.md", replacements)
    upsert_managed_block(project_root / "AGENTS.md", agents_block)

    if args.install_stop_hook:
        install_repo_stop_hook(project_root, args.autodev_dir)


if __name__ == "__main__":
    main()
