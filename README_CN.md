# Dev Review Bootstrap

[English](./README.md) | 中文

**初始化一套 Codex-first 的 autodev loop：主 orchestrator 加硬隔离的 `dev` / `reviewer` 子 agent。**

这个 skill 会把一套最小化的 orchestrator 脚手架安装到任意仓库中。它给主 agent 提供稳定的任务计划、机器可读的循环状态文件、append-only 事件日志、两个 project-scoped custom subagent，以及一个可选的 repo-local Codex `Stop` hook，用来把自动推进保持到任务完成或阻塞为止。

- **先有计划** —— 用 `plan.yaml` 装下单任务或任务列表
- **状态显式化** —— 用 `state.json` 和 `log.jsonl` 代替隐藏的进程记忆
- **硬隔离职责** —— 安装 `autodev_dev` 和 `autodev_reviewer` 两个 project-scoped custom agent
- **Codex 可自动续跑** —— repo-local `Stop` hook 可以让 orchestrator 不用全局配置就继续跑

memory 文件本身是可移植的，但这套打包好的运行时接线是 Codex-first，因为它依赖 Codex custom agents 和 Codex `Stop` hook。

## 两层结构

这套 workflow 分成两层：

- `Setup layer`
  由 bootstrap agent 安装脚手架、询问配置、校验生成文件，然后结束。
- `Runtime layer`
  由一个新的主 Codex session 读取项目内生成的文件，并作为 orchestrator 启动循环。

---

## Skill 安装方式

### 通过 Agent 安装

在 Claude Code、Codex、OpenClaw 等支持 Skill 安装的 Agent 中，直接发送：

```text
安装这个 skill：https://github.com/HoYiShui/dev-review-bootstrap
```

如果你的 Agent 支持通过 GitHub 仓库 URL 直接安装 skill，这应该是默认推荐方式。

### 手动安装

1. 在本仓库的 Releases 页面下载最新的 `.skill` 安装包：
   `https://github.com/HoYiShui/dev-review-bootstrap/releases`
2. 将 `.skill` 文件放到对应工具的 Skills 目录中。

常见路径如下：

| 工具 | 路径 |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Codex | `~/.agents/skills/` |

如果你的工具使用的是自定义 Skills 目录，请以实际配置为准。

---

## 快速开始

把 skill 安装到你的 Agent 之后：

### 第 1 步：进入目标项目

进入你想安装这套 workflow 的仓库：

```bash
cd /path/to/your/project
```

### 第 2 步：安装脚手架

#### 推荐 Prompt

```text
Use $dev-review-bootstrap to install the autodev loop for this repo.
Seed plan.yaml from this task list:
- Task one
- Task two
- Task three
```

#### 可替代 Prompt

```text
Set up the dev-review-bootstrap scaffold for this repository.
Ask only the critical bootstrap questions, install the repo-local Stop hook, and keep the plan small.
```

你的 agent 会先问几个必要问题，然后自动安装脚手架。

### 第 3 步：新开一个 orchestrator session

最佳实践是 bootstrap 完成后，新开一个 session 来跑 runtime。

在仓库根目录启动一个新的 Codex session，然后发送：

```text
Read AGENTS.md and .codex/autodev/ORCHESTRATOR.md, then run the autodev loop until plan.yaml is done or blocked.
```

等价的更明确 prompt 是：

```text
Read AGENTS.md and .codex/autodev/ORCHESTRATOR.md.
Act as the repository orchestrator.
Use the custom subagents autodev_dev and autodev_reviewer.
Continue the autodev loop until plan.yaml is done, paused, or blocked.
```

在 Codex 里，orchestrator 运行时应显式使用 `autodev_dev` 和 `autodev_reviewer` 这两个 project-scoped custom agent。如果安装了 repo-local `Stop` hook，这个新的 orchestrator session 可以自动续跑。

---

## 这个 Skill 会先问什么

在写文件之前，这个 skill 只会问最少量、但足够让脚手架可用的问题：

1. 项目根目录应该用哪个路径？
2. `plan.yaml` 应该如何初始化？
3. 是否要在 `.codex/hooks.json` 里安装 repo-local Codex `Stop` hook？
4. 项目的测试命令是什么？如果没有，是否留空？
5. 如果你在 bootstrap 阶段就提供了任务，每条任务的 review 验收标准是什么？

默认值：

- autodev 目录：`.codex/autodev`
- plan 初始化模式：`empty`
- repo-local Stop hook：开启
- memory 拆分：`plan.yaml`、`state.json`、`log.jsonl`
- subagent：`autodev_dev`、`autodev_reviewer`

安装结束后，bootstrap agent 还应该明确告诉你：去新开一个 orchestrator session，并把准确的 runtime prompt 发给你。

---

## 功能

- **项目内 autodev 脚手架** —— 在 `.codex/autodev/` 下生成计划、状态、日志、orchestrator 指南和 hook 目标
- **项目级 custom agents** —— 在 `.codex/agents/` 下生成 `autodev_dev.toml` 和 `autodev_reviewer.toml`
- **托管的 `AGENTS.md` 区块** —— 告诉主 agent 在 loop 激活时充当 orchestrator
- **任务自动推进** —— review 通过后，orchestrator 会继续推进下一个 planned task
- **文件驱动 memory** —— dev summary 和 review findings 保存在 `log.jsonl` 与 `state.json` 中
- **repo-local Codex hook** —— `.codex/hooks.json` 可以自动续跑，而不用改全局配置

---

## 安装

### 依赖

- 如果要用完整的 custom-subagent + repo-local-hook 工作流，需要 Codex
- 如果只想复用 memory scaffold，则任意支持 skill 的 coding agent 都可以
- Python 3，用于执行 bootstrap 脚本
- 如果想启用自动续跑，需要 Codex hook 支持

### 验证安装是否生效

在任意仓库中打开你的 Agent，然后输入：

```text
Use $dev-review-bootstrap to install the autodev loop for this project.
```

如果 skill 已经正确安装，你的 Agent 应该会直接进入 bootstrap 流程，而不是把它当成普通自然语言请求。

---

## 安装后会生成什么

运行这个 skill 之后，项目里应该出现：

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
└── hooks.json   # 可选，仅在启用 hook 接线时生成

AGENTS.md
```

这个 skill 会向 `AGENTS.md` 里插入一个托管区块，而不是直接覆盖整个文件。

---

## Workflow Memory

这套脚手架把 memory 拆成几个职责稳定的小文件。

| 文件 | 作用 |
| --- | --- |
| `.codex/autodev/plan.yaml` | 任务真相源 |
| `.codex/autodev/state.json` | 压缩后的机器状态 |
| `.codex/autodev/log.jsonl` | dev/review 的 append-only 事件记忆 |
| `.codex/autodev/ORCHESTRATOR.md` | orchestrator 的运行契约 |
| `.codex/agents/autodev_dev.toml` | implementation subagent 的硬 system prompt |
| `.codex/agents/autodev_reviewer.toml` | read-only reviewer 的硬 system prompt |
| `.codex/hooks.json` | 可选的 repo-local Codex 续跑 hook |

完整设计见 [references/workflow-memory.md](references/workflow-memory.md)。

---

## 工作原理

1. 主 session 作为 orchestrator。
2. 它拉起 `autodev_dev` 处理当前任务，并把返回的 JSON 结果写进 `log.jsonl`。
3. 然后它拉起只读的 `autodev_reviewer`，再把 verdict 写进 `log.jsonl`。
4. 如果 review 要求修改，同一个任务继续下一轮 dev。
5. 如果 review 接受，orchestrator 把当前任务标记为 done，并推进下一个任务。
6. `state.json` 维持最小状态，并告诉 Codex 是否应该自动续跑。
7. 只有当计划完成、暂停，或被外部因素阻塞时，这个 loop 才会停止。
8. 如果 orchestrator 第一次启动时看到空 plan，它应先向用户追问任务列表，以及每条任务的验收标准，然后再开始运行。

---

## 仓库结构

```text
dev-review-bootstrap/
├── SKILL.md
├── README.md
├── README_CN.md
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

## 输出结果

运行这个 skill 之后，得到的不是一份文档，而是一套可运行的 scaffold：

- 项目内 autodev 文件
- 项目级 custom agent profile
- 托管的 `AGENTS.md` 区块
- 可选的 repo-local Codex hook 接线

安装完成后，你就可以在 Codex 中启动一套 plan 驱动的 autodev loop。其他 agent 可以复用 memory contract，但打包好的 subagent 和 hook 接线是 Codex-specific 的。

---

## 贡献

欢迎继续改进这套 skill。比较有价值的方向包括：

- 优化 plan 和 state schema
- 改进 bootstrap 询问逻辑
- 收紧 orchestrator contract
- 改进长循环下的自动续跑策略
