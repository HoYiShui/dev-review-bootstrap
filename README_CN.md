# Dev Review Bootstrap

[English](./README.md) | 中文

**想给 Codex、Claude Code 或类似 coding agent 建立一套可重复的开发 + 审查循环？一步完成初始化。**

这个 skill 用来把一套“文件驱动”的 dev-review 工作流安装到任意仓库中。它会生成结构化 handoff 状态、workflow memory、reviewer hooks，以及适用于“常驻 dev agent + 短生命周期 reviewer agent”的项目脚手架。

- **不需要手工接线** —— 自动生成 workflow 文件、脚本以及托管的 `AGENTS.md` 区块
- **把 memory 放在文件里** —— 使用 `schedule.yaml`、`active_context`、`dev_handoff`、`open_findings`，而不是依赖进程上下文
- **无需常驻第二个 agent** —— 在回合边界触发一个短生命周期 reviewer 子进程

生成出来的 workflow 本身是 agent-agnostic 的。你可以在 Codex、Claude Code、OpenClaw 以及其他支持 skill 的 coding agent 中安装和使用它。

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

### 第 2 步：把下面的 Prompt 发给你的 Agent

#### 推荐 Prompt

```text
Use $dev-review-bootstrap to set up the dev-review workflow for this project.
```

#### 可替代 Prompt

```text
Set up the dev-review-bootstrap workflow for this repository.
Ask me only the critical bootstrap questions, then install the scaffold.
```

你的 agent 会先问几个必要问题，然后自动安装脚手架。

---

## 示例提示词

### 最简安装

```text
Use $dev-review-bootstrap to set up the workflow for this repo. Keep defaults and create an empty schedule.
```

### 用一个任务初始化

```text
Use $dev-review-bootstrap to install the workflow and seed the first task as:
"Implement the review bootstrap skill README."
```

### 用任务列表初始化

```text
Use $dev-review-bootstrap to set up the workflow. Seed schedule.yaml from this task list:
- Build the bootstrap skill
- Add README
- Test hook installation
```

### 安装可选的 Stop Dispatcher

```text
Use $dev-review-bootstrap to set up the workflow and install the user-level Stop dispatcher.
```

---

## 这个 Skill 会先问什么

在写文件之前，这个 skill 只会问最少量、但足够让脚手架可用的问题：

1. 项目根目录应该用哪个路径？
2. `schedule.yaml` 应该如何初始化？
3. 是否要安装可选的用户级 `Stop` dispatcher 到 `~/.codex/hooks.json`？
4. 项目的测试命令是什么？如果没有，是否留空？
5. 是否有额外路径需要忽略？

默认值：

- workflow 目录：`.codex/workflow`
- 触发模式：`stop`
- review artifact：JSON
- reviewer profile：留空
- schedule 初始化模式：`empty`

---

## 功能

- **项目内 workflow 脚手架** —— 在 `.codex/workflow/` 下生成状态、memory、脚本和 schema 文件
- **托管的 `AGENTS.md` 区块** —— 告诉 dev agent 去哪里读写 workflow 状态
- **结构化 review 输出** —— reviewer 会把 JSON artifact 写到 `reviews/` 下
- **压缩后的 workflow memory** —— review 后刷新 `active_context.yaml` 和 `open_findings.yaml`
- **可选的全局 dispatcher** —— 安全地向 `~/.codex/hooks.json` 添加一个 `Stop` hook 条目
- **可读的任务源** —— `schedule.yaml` 继续作为任务真相源

---

## 安装

### 依赖

- 支持 skill 的 coding agent，例如 Codex、Claude Code、OpenClaw
- Python 3，用于执行 bootstrap 脚本
- 如果想启用 hook 触发 review，需要工具本身支持 hooks

### 验证安装是否生效

在任意仓库中打开你的 Agent，然后输入：

```text
Use $dev-review-bootstrap to set up the dev-review workflow for this project.
```

如果 skill 已经正确安装，你的 Agent 应该会直接进入 bootstrap 流程，而不是把它当成普通自然语言请求。

---

## 安装后会生成什么

运行这个 skill 之后，项目里应该出现：

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

这个 skill 会向 `AGENTS.md` 里插入一个托管区块，而不是直接覆盖整个文件。

---

## Workflow Memory

这套脚手架把 memory 按职责拆开，而不是塞进一个不断膨胀的大 log 文件里。

| 文件 | 作用 |
| --- | --- |
| `schedule.yaml` | 任务真相源 |
| `state/active_context.yaml` | 下一回合 dev 的压缩状态 |
| `state/dev_handoff.yaml` | dev 单回合交接 |
| `state/open_findings.yaml` | 尚未解决的 reviewer 问题 |
| `reviews/<turn_id>.json` | 结构化 review artifact |

完整设计见 [references/workflow-memory.md](references/workflow-memory.md)。

---

## 工作原理

1. dev agent 执行当前任务。
2. 在一个较完整的实现回合结束前，更新 `state/dev_handoff.yaml`。
3. `Stop` hook 可以触发一个短生命周期 reviewer 子进程。
4. reviewer 读取当前 workflow 文件和仓库 diff。
5. reviewer 把结构化 artifact 写入 `reviews/`。
6. memory 刷新步骤更新 `active_context.yaml` 和 `open_findings.yaml`。
7. 下一个 dev 回合从文件驱动状态恢复，而不是依赖隐藏的进程记忆。

这个 skill 只负责 bootstrap 结构，不负责运行时编排。

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
│   ├── init_workflow.py
│   └── dispatch_stop_hook.py
├── references/
│   └── workflow-memory.md
└── assets/
    └── templates/
```

---

## 输出结果

运行这个 skill 之后，得到的不是一份文档，而是一套可运行的 scaffold：

- 项目内 workflow 文件
- 项目内 hook 脚本
- 托管的 `AGENTS.md` 区块
- 可选的用户级 `Stop` dispatcher 接线

安装完成后，你就可以在 Codex、Claude Code、OpenClaw 或类似 coding agent 环境中使用“常驻 dev + 临时 reviewer”的循环。

---

## 贡献

欢迎继续改进这套 skill。比较有价值的方向包括：

- 优化 workflow memory schema
- 改进 bootstrap 询问逻辑
- 扩展更多 trigger mode
- 强化 reviewer artifact 和 memory refresh 逻辑
