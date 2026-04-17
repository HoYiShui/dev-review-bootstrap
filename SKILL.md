---
name: dev-review-bootstrap
description: Install a Codex-first autodev loop scaffold into a project. Use when Codex needs to turn a task list into a self-advancing dev-review loop driven by `plan.yaml`, `state.json`, `log.jsonl`, project-scoped custom agents, `AGENTS.md`, and a repo-local `Stop` hook continuation. Trigger when the user asks to "set up autodev loop", "bootstrap orchestrator workflow", "install plan-driven dev-review loop", "install dev and reviewer subagents", "initialize autodev memory", or explicitly invokes $dev-review-bootstrap.
---

# Dev Review Bootstrap

## Overview

Install a minimal project-local scaffold for an orchestrator-style autodev loop:

- `plan.yaml` as the task source of truth
- `state.json` as the machine-owned loop state
- `log.jsonl` as append-only dev/review memory
- `.codex/agents/autodev_dev.toml` and `.codex/agents/autodev_reviewer.toml` as hard role separation
- `ORCHESTRATOR.md` plus a managed `AGENTS.md` block
- an optional repo-local Codex `Stop` hook for automatic continuation

This skill is a bootstrapper. It installs the structure and wiring. It does not become the runtime orchestrator.

Treat the workflow as two layers:

- `Setup layer`
  Bootstrap only. Install files, ask the minimum questions, verify the scaffold, and hand off to the user.
- `Runtime layer`
  A fresh main session becomes the orchestrator by reading the generated project files.

## Ask First

Before writing files, ask only the minimum questions needed to make the scaffold usable. Prefer this order:

1. Confirm the project root if the current directory is ambiguous.
2. Ask how to seed `plan.yaml`.
3. Ask whether to install the repo-local Codex `Stop` hook in `.codex/hooks.json`.
4. Ask for the project test command, or confirm it should stay blank.

Use defaults unless the user wants to customize them:

- autodev dir: `.codex/autodev`
- task memory split: `plan.yaml`, `state.json`, `log.jsonl`
- hook mode: repo-local `Stop`
- initial task source: `empty`
- test command: blank

If the user has already supplied enough information in the request, do not ask again.

## Seed `plan.yaml`

Support exactly these plan seed modes:

- `empty`
  Create an empty task list and leave the loop idle.
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
  --plan-mode <empty|single-task|task-list> \
  [--task-title "..."] \
  [--task-list-file <path>] \
  [--test-command "..."] \
  [--autodev-dir ".codex/autodev"] \
  [--install-stop-hook]
```

Use `scripts/init_workflow.py` instead of hand-writing the scaffold. The script:

- creates `.codex/autodev/`
- writes `plan.yaml`, `state.json`, `log.jsonl`, and `ORCHESTRATOR.md`
- writes project-scoped custom agents under `.codex/agents/`
- adds or updates a managed block in `AGENTS.md`
- writes the repo-local `stop.py` hook target
- optionally installs a repo-local `.codex/hooks.json` entry for automatic continuation in Codex

If files already exist, inspect them first. Do not overwrite non-empty workflow files unless the user explicitly asks.

## Verify After Install

After running the installer:

1. Read the generated `AGENTS.md` block.
2. Read `.codex/autodev/plan.yaml`.
3. Read `.codex/autodev/state.json`.
4. Read `.codex/autodev/ORCHESTRATOR.md`.
5. Read `.codex/agents/autodev_dev.toml` and `.codex/agents/autodev_reviewer.toml`.
6. If the user asked for hook wiring, confirm `.codex/hooks.json` points at `.codex/autodev/hooks/stop.py`.

If the user asked for initial tasks, verify they landed in `plan.yaml`.

## Required Handoff To The User

At the end of bootstrap, explicitly tell the user that setup is complete and that runtime should start in a fresh session.

Do not quietly assume the current bootstrap session should continue as the orchestrator unless the user explicitly asks for that.

Give the user a concrete next step. Use wording equivalent to:

```text
Bootstrap is complete. Start a new Codex session at the repository root and send:

Read AGENTS.md and .codex/autodev/ORCHESTRATOR.md.
Act as the repository orchestrator.
Use the custom subagents autodev_dev and autodev_reviewer.
Continue the autodev loop until plan.yaml is done, paused, or blocked.
```

If the repo-local `Stop` hook was installed, mention that the new orchestrator session can auto-continue across turns.

## Runtime Boundaries

Keep these boundaries explicit when explaining or adjusting the scaffold:

- the main agent owns `plan.yaml`, `state.json`, and `log.jsonl`
- `autodev_dev` implements the current task and returns structured JSON
- `autodev_reviewer` stays read-only and returns `accepted`, `changes_requested`, or `blocked`
- the hook only keeps the orchestrator alive; it is not the orchestrator

The setup layer should point the runtime layer at:

- `AGENTS.md`
- `.codex/autodev/ORCHESTRATOR.md`
- `.codex/autodev/plan.yaml`
- `.codex/autodev/state.json`
- `.codex/autodev/log.jsonl`

Do not silently install a user-level global hook. This skill should default to repo-local wiring.

## Read More Only When Needed

- Read [references/workflow-memory.md](references/workflow-memory.md) when the user wants to change the memory model, event schema, or loop states.
- Read `assets/templates/` only when you need to inspect or patch the generated files.
