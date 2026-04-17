---
name: dev-review-bootstrap
description: Install a reusable dev-review workflow scaffold into a project. Use when Codex needs to set up a repository so a long-lived dev agent can hand off structured state, a hook-triggered reviewer can run as a short-lived subprocess, and workflow memory lives in project files instead of process context. Trigger when the user asks to "set up dev-review workflow", "bootstrap review infrastructure", "install handoff/reviewer hooks", "initialize workflow memory", or explicitly invokes $dev-review-bootstrap.
---

# Dev Review Bootstrap

## Overview

Install a project-local workflow scaffold for:

- a long-lived dev agent
- a short-lived reviewer agent triggered at turn boundaries
- file-backed workflow memory (`schedule.yaml`, `active_context`, `dev_handoff`, `open_findings`)

This skill is a bootstrapper. It installs the structure and wiring. It does not become the runtime orchestrator.

## Ask First

Before writing files, ask only the minimum questions needed to make the scaffold usable. Prefer this order:

1. Confirm the project root if the current directory is ambiguous.
2. Ask how to seed `schedule.yaml`.
3. Ask whether to install the user-level `Stop` dispatcher in `~/.codex/hooks.json`.
4. Ask for the project test command, or confirm it should stay blank.
5. Ask for any extra paths the workflow should ignore.

Use defaults unless the user wants to customize them:

- workflow dir: `.codex/workflow`
- memory files: YAML
- review artifact: JSON
- trigger mode: `stop`
- reviewer profile: blank
- initial task source: `empty`
- ignored paths: `reviews`, `.codex/workflow`, `.git`, `node_modules`, `dist`, `build`

If the user has already supplied enough information in the request, do not ask again.

## Seed `schedule.yaml`

Support exactly these schedule seed modes:

- `empty`
  Create the schema with a placeholder task.
- `single-task`
  Create one initial task from the user's request.
- `task-list`
  Create multiple tasks from a user-provided list.

If the user says "set up the workflow first" without giving tasks, use `empty`.

## Install the Scaffold

Run:

```bash
python3 scripts/init_workflow.py \
  --project-root <repo-root> \
  --schedule-mode <empty|single-task|task-list> \
  [--task-title "..."] \
  [--task-list-file <path>] \
  [--test-command "..."] \
  [--reviewer-profile "..."] \
  [--workflow-dir ".codex/workflow"] \
  [--install-stop-dispatcher]
```

Use `scripts/init_workflow.py` instead of hand-writing the scaffold. The script:

- creates `.codex/workflow/`
- writes the state and memory templates
- adds or updates a managed block in `AGENTS.md`
- installs project-local hook scripts
- optionally installs a user-level `Stop` dispatcher in `~/.codex/hooks.json`

If files already exist, inspect them first. Do not overwrite non-empty workflow files unless the user explicitly asks.

## Verify After Install

After running the installer:

1. Read the generated `AGENTS.md` block.
2. Read `.codex/workflow/schedule.yaml`.
3. Read `.codex/workflow/workflow.env`.
4. Confirm the project-local hook scripts exist.
5. If the user asked for hook wiring, confirm the dispatcher entry exists in `~/.codex/hooks.json`.

If the user asked for an initial task, verify the task title landed in `schedule.yaml`.

## Runtime Boundaries

Keep these boundaries explicit when explaining or adjusting the scaffold:

- `dev` writes `state/dev_handoff.yaml`
- `reviewer` writes a structured review artifact under `reviews/`
- the hook refreshes `state/active_context.yaml` and `state/open_findings.yaml`
- `schedule.yaml` is the task source of truth and may still need intentional edits by the user or a coordinator

Do not silently edit `~/.codex/config.toml` to create reviewer profiles unless the user explicitly asks.

## Read More Only When Needed

- Read [references/workflow-memory.md](references/workflow-memory.md) when the user wants to change the memory model, file schema, or task states.
- Read `assets/templates/` only when you need to inspect or patch the generated files.
