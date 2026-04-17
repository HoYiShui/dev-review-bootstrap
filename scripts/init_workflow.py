#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
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


def build_schedule(mode: str, task_title: str, task_list: list[str]) -> str:
    if mode == "empty":
        return render_template(
            "schedule.yaml",
            {
                "CURRENT_TASK_ID": "T1",
                "CURRENT_TASK_TITLE": "Replace with the first task",
                "CURRENT_TASK_STATUS": "planned",
            },
        )

    if mode == "single-task":
        title = task_title or "Initial task"
        return render_template(
            "schedule.yaml",
            {
                "CURRENT_TASK_ID": "T1",
                "CURRENT_TASK_TITLE": title,
                "CURRENT_TASK_STATUS": "in_progress",
            },
        )

    if not task_list:
        raise SystemExit("task-list mode requires at least one task")

    lines = ["current_task: T1", "tasks:"]
    for index, title in enumerate(task_list, start=1):
        task_id = f"T{index}"
        status = "in_progress" if index == 1 else "planned"
        lines.extend(
            [
                f"  - id: {task_id}",
                f"    title: {json.dumps(title)}",
                f"    status: {status}",
                "    priority: 1",
                "    exit_criteria:",
                "      - dev_handoff_written",
                "      - no_blocking_findings",
            ]
        )
    return "\n".join(lines) + "\n"


def install_stop_dispatcher() -> None:
    hooks_path = Path.home() / ".codex" / "hooks.json"
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    if hooks_path.exists():
        data = json.loads(hooks_path.read_text())
    else:
        data = {"hooks": {}}

    hooks = data.setdefault("hooks", {})
    stop_rules = hooks.setdefault("Stop", [])
    command = f"python3 {shlex.quote(str(SKILL_DIR / 'scripts' / 'dispatch_stop_hook.py'))}"

    for rule in stop_rules:
        for hook in rule.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command") == command:
                hooks_path.write_text(json.dumps(data, indent=2) + "\n")
                return

    stop_rules.append({"hooks": [{"type": "command", "command": command}]})
    hooks_path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--workflow-dir", default=".codex/workflow")
    parser.add_argument(
        "--schedule-mode",
        choices=["empty", "single-task", "task-list"],
        default="empty",
    )
    parser.add_argument("--task-title", default="")
    parser.add_argument("--task-list-file")
    parser.add_argument("--trigger-mode", choices=["stop", "manual"], default="stop")
    parser.add_argument("--test-command", default="")
    parser.add_argument("--reviewer-profile", default="")
    parser.add_argument("--install-stop-dispatcher", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    workflow_dir = project_root / args.workflow_dir
    state_dir = workflow_dir / "state"
    hooks_dir = workflow_dir / "hooks"
    reviews_dir = project_root / "reviews"

    task_list = []
    if args.task_list_file:
        task_list = load_task_list(Path(args.task_list_file).resolve())

    schedule_text = build_schedule(args.schedule_mode, args.task_title, task_list)
    task_title_for_context = args.task_title or (task_list[0] if task_list else "Replace with the first task")
    task_status = "in_progress" if args.schedule_mode != "empty" else "planned"

    replacements = {
        "WORKFLOW_DIR": args.workflow_dir,
        "TRIGGER_MODE": args.trigger_mode,
        "REVIEWER_PROFILE": args.reviewer_profile,
        "TEST_COMMAND": args.test_command,
        "CURRENT_TASK_ID": "T1",
        "CURRENT_TASK_GOAL": task_title_for_context,
        "CURRENT_NEXT_STEP": "Update state/dev_handoff.yaml after the next substantial change",
    }

    state_dir.mkdir(parents=True, exist_ok=True)
    hooks_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)

    write_text(workflow_dir / "schedule.yaml", schedule_text, overwrite=args.force)
    write_text(
        workflow_dir / "workflow.env",
        render_template("workflow.env", replacements),
        overwrite=args.force,
    )
    write_text(
        state_dir / "active_context.yaml",
        render_template("active_context.yaml", replacements),
        overwrite=args.force,
    )
    write_text(
        state_dir / "dev_handoff.yaml",
        render_template("dev_handoff.yaml", replacements),
        overwrite=args.force,
    )
    write_text(
        state_dir / "open_findings.yaml",
        render_template("open_findings.yaml", replacements),
        overwrite=args.force,
    )
    write_text(
        workflow_dir / "review_schema.json",
        render_template("review_schema.json", replacements),
        overwrite=args.force,
    )
    write_text(
        hooks_dir / "post_stop.sh",
        render_template("post_stop.sh", replacements),
        overwrite=args.force,
    )
    write_text(
        hooks_dir / "run_reviewer.sh",
        render_template("run_reviewer.sh", replacements),
        overwrite=args.force,
    )
    write_text(
        hooks_dir / "update_memory.py",
        render_template("update_memory.py", replacements),
        overwrite=args.force,
    )

    for path in [
        hooks_dir / "post_stop.sh",
        hooks_dir / "run_reviewer.sh",
        hooks_dir / "update_memory.py",
    ]:
        path.chmod(0o755)

    agents_block = render_template("project-agents-block.md", replacements)
    upsert_managed_block(project_root / "AGENTS.md", agents_block)

    if args.install_stop_dispatcher:
        install_stop_dispatcher()


if __name__ == "__main__":
    main()
