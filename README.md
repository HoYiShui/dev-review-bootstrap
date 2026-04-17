# Dev Review Bootstrap

English | [中文](./README_CN.md)

**Bootstrap a Codex-first autodev loop with a main orchestrator plus hard `dev` and `reviewer` subagents.**

Use this skill to install a minimal orchestrator scaffold into any repository. It gives the main agent a stable task plan, a machine-owned loop state file, an append-only event log, two project-scoped custom subagents, and an optional repo-local Codex `Stop` hook that keeps the loop running until the plan is done or blocked.

- **Plan first** — seed `plan.yaml` with one task or a full task list
- **Keep state explicit** — use `state.json` and `log.jsonl` instead of hidden process memory
- **Hard role separation** — install `autodev_dev` and `autodev_reviewer` as project-scoped custom agents
- **Auto-continue in Codex** — repo-local `Stop` hook can keep the orchestrator alive without global config

The memory files are portable, but the bundled runtime wiring is Codex-first because it relies on Codex custom agents and the Codex `Stop` hook.

## Two Layers

This workflow has two distinct layers:

- `Setup layer`
  A bootstrap agent installs the scaffold, asks the configuration questions, verifies the files, and stops.
- `Runtime layer`
  A fresh main Codex session becomes the orchestrator by reading the generated project files and then running the loop.

---

## Skill Installation

### Install via Agent

In Claude Code, Codex, OpenClaw, or another agent that supports skill installation from GitHub, send:

```text
Install this skill: https://github.com/HoYiShui/dev-review-bootstrap
```

If your agent supports direct skill installation from a repository URL, this should be the default path.

### Manual Install

1. Download the latest `.skill` package from this repository's Releases page:
   `https://github.com/HoYiShui/dev-review-bootstrap/releases`
2. Put the `.skill` file into the appropriate Skills directory for your tool.

Typical skill directories:

| Tool | Skills path |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Codex | `~/.agents/skills/` |

If your tool uses a custom skills directory, use that instead.

---

## Quick Start

After the skill is installed into your agent:

### Step 1: Open the Project You Want to Scaffold

Go to the repository where you want the workflow installed:

```bash
cd /path/to/your/project
```

### Step 2: Install the Scaffold

#### Recommended Prompt

```text
Use $dev-review-bootstrap to install the autodev loop for this repo.
Seed plan.yaml from this task list:
- Task one
- Task two
- Task three
```

#### Alternative Prompt

```text
Set up the dev-review-bootstrap scaffold for this repository.
Ask only the critical bootstrap questions, install the repo-local Stop hook, and keep the plan small.
```

Your agent will ask a few setup questions, then install the scaffold.

### Step 3: Open A Fresh Orchestrator Session

Best practice is to start the runtime in a new session after bootstrap finishes.

Open a new Codex session at the repository root, then send:

```text
Read AGENTS.md and .codex/autodev/ORCHESTRATOR.md, then run the autodev loop until plan.yaml is done or blocked.
```

Equivalent explicit prompt:

```text
Read AGENTS.md and .codex/autodev/ORCHESTRATOR.md.
Act as the repository orchestrator.
Use the custom subagents autodev_dev and autodev_reviewer.
Continue the autodev loop until plan.yaml is done, paused, or blocked.
```

In Codex, the orchestrator should use the project-scoped custom agents `autodev_dev` and `autodev_reviewer`. If the repo-local `Stop` hook is installed, that new orchestrator session can continue automatically across turns.

---

## What the Skill Asks

Before writing files, the skill asks only the minimum questions needed to make the scaffold usable:

1. What project root should be used?
2. How should `plan.yaml` be seeded?
3. Should it install the repo-local Codex `Stop` hook in `.codex/hooks.json`?
4. What test command should the project use, if any?
5. If you already provide tasks during bootstrap, what are the review acceptance criteria for each task?

Defaults:

- autodev dir: `.codex/autodev`
- plan seed mode: `empty`
- repo-local Stop hook: `on`
- task memory split: `plan.yaml`, `state.json`, `log.jsonl`
- subagents: `autodev_dev`, `autodev_reviewer`

After installation, the bootstrap agent should also tell you to open a fresh orchestrator session and give you the exact runtime prompt to send there.

---

## Features

- **Project-local autodev scaffold** — creates `.codex/autodev/` with the plan, state, log, orchestrator guide, and hook target
- **Project-scoped custom agents** — creates `.codex/agents/autodev_dev.toml` and `.codex/agents/autodev_reviewer.toml`
- **Managed `AGENTS.md` block** — tells the main agent to behave as the orchestrator when the loop is active
- **Task progression** — after an accepted review, the orchestrator advances to the next planned task
- **File-backed memory** — review findings and dev summaries stay in `log.jsonl` and `state.json`
- **Repo-local Codex hook** — `.codex/hooks.json` can auto-continue without touching global configuration

---

## Installation

### Requirements

- Codex for the full custom-subagent plus repo-local-hook workflow
- A coding agent with skill support if you only want the memory scaffold
- Python 3 for the bootstrap scripts
- Codex hook support if you want automatic continuation

### Verify Installation

Open any repository in your agent and invoke:

```text
Use $dev-review-bootstrap to install the autodev loop for this project.
```

If the skill is installed correctly, your agent should start the bootstrap flow instead of treating this as a generic request.

---

## What Gets Installed

After running the skill in a project, you should see:

```text
.codex/
├── agents/
│   ├── autodev_dev.toml
│   └── autodev_reviewer.toml
├── autodev/
│   ├── ORCHESTRATOR.md
│   ├── plan.yaml
│   ├── state.json
│   ├── log.jsonl
│   └── hooks/
│       └── stop.py
└── hooks.json   # optional, only when hook wiring is enabled

AGENTS.md
```

The skill adds a managed block to `AGENTS.md` instead of replacing the whole file.

---

## Workflow Memory

This scaffold keeps memory small and role-specific.

| File | Purpose |
| --- | --- |
| `.codex/autodev/plan.yaml` | task source of truth |
| `.codex/autodev/state.json` | compressed machine-owned loop state |
| `.codex/autodev/log.jsonl` | append-only dev/review event memory |
| `.codex/autodev/ORCHESTRATOR.md` | runtime contract for the orchestrator |
| `.codex/agents/autodev_dev.toml` | hard system prompt for the implementation subagent |
| `.codex/agents/autodev_reviewer.toml` | hard system prompt for the read-only reviewer |
| `.codex/hooks.json` | optional repo-local Codex continuation hook |

For the full design, see [references/workflow-memory.md](references/workflow-memory.md).

---

## How It Works

1. The main session acts as orchestrator.
2. It spawns `autodev_dev` for the current task and records the returned JSON into `log.jsonl`.
3. It then spawns `autodev_reviewer` in read-only mode and records the verdict into `log.jsonl`.
4. If review requests changes, the same task stays active and another dev pass starts.
5. If review accepts, the orchestrator marks the task done and advances the next one in `plan.yaml`.
6. `state.json` stays small and tells Codex whether the loop should auto-continue.
7. The loop stops only when the plan is done, paused, or blocked.
8. If the first orchestrator start sees an empty plan, it should ask for the task list and the per-task acceptance criteria before running anything.

---

## Repository Structure

```text
dev-review-bootstrap/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── init_workflow.py
├── references/
│   └── workflow-memory.md
└── assets/
    └── templates/
```

---

## Output

Running the skill produces a working scaffold, not just documentation:

- project-local autodev files
- project-scoped custom agent profiles
- a managed `AGENTS.md` block
- optional repo-local Codex hook wiring

Once installed, you can start a plan-driven autodev loop in Codex. Other agents can reuse the memory contract, but the included subagent and hook wiring is Codex-specific.

---

## Contributing

Suggestions and improvements are welcome. Useful contributions include:

- refining the plan and state schema
- improving the bootstrap questions
- tightening the orchestrator contract
- improving the continuation strategy for long-running loops
