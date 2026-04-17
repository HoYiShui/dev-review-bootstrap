#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def yaml_scalar(value):
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def dump_yaml(data, indent=0):
    lines = []
    prefix = " " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                if isinstance(value, list) and not value:
                    lines[-1] = f"{prefix}{key}: []"
                elif isinstance(value, dict) and not value:
                    lines[-1] = f"{prefix}{key}: {{}}"
                else:
                    lines.extend(dump_yaml(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-dir", required=True)
    parser.add_argument("--review-file", required=True)
    args = parser.parse_args()

    workflow_dir = Path(args.workflow_dir)
    review_file = Path(args.review_file)
    review = json.loads(review_file.read_text())

    findings = []
    for finding in review.get("blocking_findings", []):
        findings.append(
            {
                "id": finding["id"],
                "task_id": review["task_id"],
                "severity": finding["severity"],
                "title": finding["title"],
                "status": "open",
                "source_turn_id": review["turn_id"],
                "evidence": finding["evidence"],
                "recommended_action": finding["recommended_action"],
            }
        )

    active_context = {
        "task_id": review["task_id"],
        "goal": review["summary"],
        "current_constraints": [
            "reviewer must remain read-only",
            "dev must write state/dev_handoff.yaml before ending the turn",
        ],
        "next_step": review["next_step"],
        "must_watch": [finding["id"] for finding in findings],
    }

    open_findings = {"findings": findings}

    (workflow_dir / "state" / "active_context.yaml").write_text(
        "\n".join(dump_yaml(active_context)) + "\n"
    )
    (workflow_dir / "state" / "open_findings.yaml").write_text(
        "\n".join(dump_yaml(open_findings)) + "\n"
    )


if __name__ == "__main__":
    main()
