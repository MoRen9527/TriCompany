<!-- GOVERNANCE: 本文件真源在 TriCompany/docs/project-sources/，项目侧副本经 FADE-002 发布域管线（project-source-doc-sync-manifest）字节发布，禁直接修改项目侧——变更一律改真源后走管线发布。 -->

# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

TriMetaverse is a multi-module AI-native development platform. It contains:

- **TriRLC** — Local Controller daemon (HTTP + SSE agent loop, heartbeat, cron, session reaper). Located in sibling repo `../TriRLC/`（原 TriLC，2026-08-31 改名）.
- **TriPilot** — VS Code / VSCodium chat extension. Located in sibling repo `../TriPilot/`.
- **TriCode** — Shared code runtime and orchestration. Located in sibling repo `../TriCode/`.
- **TriCade** — Desktop distribution bundle (TriRLC + TriPilot + TriCode packaged for Windows).
- **TriCompany** — Cyber-company operating vehicle (13 AI employees). Embedded in `.claude/agents/` (primary runtime) and `.github/agents/` (Copilot-host entry).

Current phase & roadmap → BusinessStrategy 面: `docs/execution/v0.9.x-dual-track-tricompany-plan.md`（LG-028 迁出）.

## Module Workspace Layout

```
D:/Code/ai/
├── TriMetaverse/    ← this repo (build scripts, docs, .github/, .claude/)
├── TriRLC/          ← Local Controller daemon（原 TriLC，2026-08-31 改名）
├── TriPilot/        ← VS Code extension
├── TriCode/         ← Shared runtime
├── TriCompany/      ← Cyber-company source
└── TriMMC/         ← Meta Controller（原 TriMC，2026-09 改名；兼容面沿用旧名过渡）
```

All modules are sibling directories. Use `../<module>/` for cross-repo references.

## 董事会/董事长助理分权制（2026-08-28 CEO 立，原"编排/中枢分权制"更名）

- **董事会**（CEO 直连会话）：接收指令、投递执行、转呈交付、持有联审席位通道（CPO/CTO subagent）、紧急回滚协调——**其余一切任务性工作默认投递常驻中枢执行**。
- **董事长助理**（常驻中枢，xiaojia-hub，通信正名 COS，惯称小贾）：**董事会发出的一切指令交其执行**；持有完整工作上下文，维护挂账台账；开工前置核查含 TriCompany 协议/纪律/登记册现行版。
- **无小任务豁免**：判据口诀——「产出物的生成过程董事长助理需不需要知道？需要=投递」。
- **上下文管理**：容量交宿主 auto-compact，不盯水位不设人工压缩仪式；**受控压缩仅用于状态污染响应**（上下文新旧混杂/陈旧态复现时：先产全量快照 `.fade/hub-snapshots/` 归一，再压缩重建，董事会 diff 核验）；崩溃恢复照 SOP。协议正身：`docs/execution/fade-007-context-reservoir-spec.md`（按本教义修订口径候核）。
- 助理不可用或本文件规则与助理实际状态冲突时，以仓库治理文档为准重建助理。
- **中枢爆溃恢复 SOP**：中枢不可用时→按 `docs/execution/fade-007-context-reservoir-spec.md` §五 恢复配方重建，重建体 provisional 转正由董事会签发（SOP 正身：`docs/execution/fade-007-incident-sop.md`）。

## Registry Routing

When you need facts, follow this priority order:

1. **Central Business Strategy** — `BusinessStrategy` agent. Module boundaries, business model, experiment phase.
2. **Company Governance** — `CompanyGovernanceRegistry` agent. Org docs, naming conventions, management processes.
3. **Module Product Registry** — `<Module>ProductRegistry` agent. State, roadmap, requirements.
4. **Module Code Registry** — `TriMetaverseCodeRegistry` agent. Code structure, docs structure, quality risks.
5. **Module source code** — Read the actual code.

Key documents:
- `docs/三元宇宙架构与模块说明.md` — Architecture overview and module absorption rules
- `tricompany.md` — TriCompany design document
- `docs/github-repo-governance.md` — GitHub repo governance rules
- `docs/execution/v0.9.x-dual-track-tricompany-plan.md` — Current execution plan

## Agent Architecture

- **Registry Agents** — Impersonal data hubs. Facts, state, boundaries, indexes, memory only.
- **Role Agents** — Personal role executors. Business judgment, progress, coordination.

13 employees onboarded in TriCompany V1.0. Active runtime: `.claude/agents/` (primary), `.github/agents/` (Copilot-host entry).

## CodeGraph Usage

This project has CodeGraph enabled. Use it for structural questions:

| Intent | Tool |
|---|---|
| Symbol lookup | `codegraph_search` |
| Task/feature context | `codegraph_context` (primary) |
| Who calls X? | `codegraph_callers` |
| What does X call? | `codegraph_callees` |
| Blast radius of change | `codegraph_impact` |
| Symbol source/signature | `codegraph_node` |
| Multiple symbols at once | `codegraph_explore` |
| Directory structure | `codegraph_files` |

**Rules**: Answer directly with codegraph, don't delegate exploration. Trust codegraph results (AST-parsed). Don't grep before codegraph_search for symbol lookups.

## Source of Truth Order

1. Source-side in `TriCompany/` (canonical employee definitions, product facts, registry)
2. Published copies in this repo (`.github/`, `docs/`)
3. Runtime state in employee knowledge workspace
4. Session transcripts

When source and published copies conflict, source-side wins. When frozen source is stale, report it but don't silently override.

## Weekly Operating Records

→ COS 面（operating-records 收口域）：`docs/workflow/operating-records/<current-week>/`（LG-028 迁出，路由指针）

## Common Commands

→ CTO 面（域知识族）+CAO 纪律册：TriRLC daemon/健康检查/构建管线/安装脚本命令族（LG-028 迁出，路由指针）。
## File Conventions

→ CAO 纪律册附录（`TriCompany/docs/workflow/engineering-disciplines.md`）：commit attribution/AI co-author/markdownlint/agent 文件命名（LG-028 迁出，路由指针）。