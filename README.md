# Dev Review Bootstrap

English | [中文](./README_CN.md)

**Need a repeatable dev + review loop for Codex, Claude Code, or similar coding agents? Bootstrap it in one step.**

Use this skill to install a file-backed dev-review workflow into any repository. It sets up structured handoff state, workflow memory, reviewer hooks, and project scaffolding for a long-lived dev agent plus a short-lived reviewer agent.

- **No manual wiring** — generate the workflow files, scripts, and managed `AGENTS.md` block automatically
- **Keep memory in files** — use `schedule.yaml`, `active_context`, `dev_handoff`, and `open_findings` instead of relying on process context
- **Review without a permanent second agent** — trigger a short-lived reviewer subprocess at turn boundaries

The generated workflow is agent-agnostic. You can install and use it with Codex, Claude Code, OpenClaw, and similar skill-capable coding agents.

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

### Step 2: Send One of These Prompts to Your Agent

#### Recommended Prompt

```text
Use $dev-review-bootstrap to set up the dev-review workflow for this project.
```

#### Alternative Prompt

```text
Set up the dev-review-bootstrap workflow for this repository.
Ask me only the critical bootstrap questions, then install the scaffold.
```

Your agent will ask a few setup questions, then install the scaffold.

---

## Example Prompts

### Minimal Setup

```text
Use $dev-review-bootstrap to set up the workflow for this repo. Keep defaults and create an empty schedule.
```

### Start With One Task

```text
Use $dev-review-bootstrap to install the workflow and seed the first task as:
"Implement the review bootstrap skill README."
```

### Start With a Task List

```text
Use $dev-review-bootstrap to set up the workflow. Seed schedule.yaml from this task list:
- Build the bootstrap skill
- Add README
- Test hook installation
```

### Install the Optional Stop Dispatcher

```text
Use $dev-review-bootstrap to set up the workflow and install the user-level Stop dispatcher.
```

---

## What the Skill Asks

Before writing files, the skill asks only the minimum questions needed to make the scaffold usable:

1. What project root should be used?
2. How should `schedule.yaml` be seeded?
3. Should it install the optional user-level `Stop` dispatcher in `~/.codex/hooks.json`?
4. What test command should the project use, if any?
5. Are there any extra paths that should be ignored?

Defaults:

- workflow dir: `.codex/workflow`
- trigger mode: `stop`
- review artifact: JSON
- reviewer profile: blank
- schedule seed mode: `empty`

---

## Features

- **Project-local workflow scaffold** — creates `.codex/workflow/` with state, memory, scripts, and schema files
- **Managed `AGENTS.md` block** — tells the dev agent where to read and write workflow state
- **Structured review output** — reviewer writes JSON artifacts under `reviews/`
- **Compressed workflow memory** — refreshes `active_context.yaml` and `open_findings.yaml` after review
- **Optional global dispatcher** — adds a safe `Stop` hook entry to `~/.codex/hooks.json`
- **Human-readable task source** — keeps `schedule.yaml` as the task truth source

---

## Installation

### Requirements

- A coding agent with skill support, such as Codex, Claude Code, or OpenClaw
- Python 3 for the bootstrap scripts
- Hook support if you want hook-triggered review

### Verify Installation

Open any repository in your agent and invoke:

```text
Use $dev-review-bootstrap to set up the dev-review workflow for this project.
```

If the skill is installed correctly, your agent should start the bootstrap flow instead of treating this as a generic request.

---

## What Gets Installed

After running the skill in a project, you should see:

```text
.codex/workflow/
├── schedule.yaml
├── workflow.env
├── review_schema.json
├── state/
│   ├── active_context.yaml
│   ├── dev_handoff.yaml
│   └── open_findings.yaml
└── hooks/
    ├── post_stop.sh
    ├── run_reviewer.sh
    └── update_memory.py

reviews/
AGENTS.md
```

The skill adds a managed block to `AGENTS.md` instead of replacing the whole file.

---

## Workflow Memory

This scaffold splits memory by responsibility instead of pushing everything into one log file.

| File | Purpose |
| --- | --- |
| `schedule.yaml` | task source of truth |
| `state/active_context.yaml` | compressed state for the next dev turn |
| `state/dev_handoff.yaml` | one-turn dev handoff |
| `state/open_findings.yaml` | unresolved reviewer findings |
| `reviews/<turn_id>.json` | structured review artifact |

For the full design, see [references/workflow-memory.md](references/workflow-memory.md).

---

## How It Works

1. The dev agent works on the current task.
2. Before ending a substantial turn, it updates `state/dev_handoff.yaml`.
3. A `Stop` hook can trigger a short-lived reviewer subprocess.
4. The reviewer reads the current workflow files and the repo diff.
5. The reviewer writes a structured artifact to `reviews/`.
6. The memory refresh step updates `active_context.yaml` and `open_findings.yaml`.
7. The next dev turn resumes from file-backed state, not from hidden process memory.

This skill bootstraps the structure. It does not become the runtime orchestrator.

---

## Repository Structure

```text
dev-review-bootstrap/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── init_workflow.py
│   └── dispatch_stop_hook.py
├── references/
│   └── workflow-memory.md
└── assets/
    └── templates/
```

---

## Output

Running the skill produces a working scaffold, not just documentation:

- project-local workflow files
- project-local hook scripts
- a managed `AGENTS.md` block
- optional user-level `Stop` dispatcher wiring

Once installed, you can start using the repository with a long-lived dev agent and a short-lived reviewer loop in Codex, Claude Code, OpenClaw, or similar coding-agent setups.

---

## Contributing

Suggestions and improvements are welcome. Useful contributions include:

- refining the workflow memory schema
- improving the bootstrap questions
- expanding the installer for more trigger modes
- improving reviewer artifact and memory refresh logic
