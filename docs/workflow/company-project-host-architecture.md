# 赛博公司架构：公司-项目-宿主三层治理模型

版本：V0.1 → V1.0（已批准）
日期：2026-07-12
状态：CEO 已批准，Phase 0 完成，进入 Phase 1

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/company-project-host-architecture.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- lastSyncedAt: 2026-07-12

---

## 1. 问题诊断：当前架构的四个结构性缺陷

### 1.1 支撑包被绑定在单个项目内

当前 `TriCompany-copilot-host-assets` 的物理路径是 `TriMetaverse/TriCompany-copilot-host-assets/`——它活在 TriMetaverse 项目根目录下。这意味着公司的员工记忆、wiki 管线、四层知识空间在物理上和"一个项目"绑死了。

**症状**：如果赛博公司要在第二个项目（比如"喵次元"）里上岗同一批员工，所有 knowledge workspace 都要重新发布到新项目根目录，且两边的 wiki 是隔离的。

### 1.2 发布管线写死了目标项目路径

```powershell
python -m runtime.cognition.employee_host_publish --support-root ..\TriMetaverse\TriCompany-copilot-host-assets
```

`--support-root` 硬编码指向 TriMetaverse。发布到其他项目需要改参数，且发布逻辑不区分"公司级共享数据"和"项目级实例数据"。

### 1.3 TriDev 作为独立模块存在，实际是公司级工具

`TriDev` 提供十阶段 phase engine、模块 scaffold、部署 CLI——这些都是赛博公司开发任何项目都需要的通用工具，不是 TriMetaverse 专属。当前把它作为独立模块放在架构表中，导致：
- TriDev 的 host-assets 会再次倍增（TriDev-copilot-host-assets）
- 与 TriCompany 的工具职责边界模糊

### 1.4 .github/agents 发布缺少宿主感知层

当前 agent 发布流程是 TriCompany source → TriMetaverse/.github/agents/，但 `.github/agents/` 是 GitHub Copilot 宿主特有的发现机制。如果未来切换到 Claude Code 或 TriMC 原生宿主，agent 发现格式完全不同。当前没有中间的"宿主适配层"。

---

## 2. 三层治理模型

赛博公司的架构应该理解为三个正交的层：

```
┌──────────────────────────────────────────────────┐
│                  公司层 (Company)                  │
│               TriCompany（唯一真源）                │
│                                                    │
│  员工定义 · 治理规则 · 工作流程 · CLI工具            │
│  模块模板 · 项目模板 · 发布引擎 · 知识管线           │
└────────────┬──────────────────────────┬────────────┘
             │                          │
    ┌────────▼────────┐        ┌───────▼────────┐
    │   宿主适配层      │        │   宿主适配层     │
    │  Copilot Host   │        │   TriMC Host    │
    │                 │        │                │
    │ .github/agents/ │        │ agent.yaml     │
    │ .github/prompts/│        │ binding.json   │
    │ {proj}/TriComp- │        │ {proj}/TriComp- │
    │  any-copilot-   │        │  any-trimc-    │
    │  assets/        │        │  assets/       │
    └────────┬────────┘        └───────┬────────┘
             │                          │
    ┌────────▼──────────────────────────▼────────────┐
    │                 项目层 (Project)                 │
    │          TriMetaverse / 喵次元 / ...             │
    │                                                 │
    │  白皮书 · 模块代码 · 项目级 registry              │
    │  项目级 docs/ · README · 模块架构说明             │
    └─────────────────────────────────────────────────┘
```

### 2.1 公司层：TriCompany

**定位**：赛博公司的"操作系统"。跨项目、跨宿主复用。

| 资产类别 | 内容 | 真源路径 |
|---------|------|---------|
| 员工定义 | 五件套 (soul/memory/colleagues/social + agent.md)、contract | `.github/source-agents/<id>/` |
| 公司治理 | 秘书处、会议制度、岗位边界、发布纪律 | `docs/registry/company-governance-state.md` |
| 工作流程 | IPD 流程、host-object-publish-flow、employee-llm-wiki-guide | `docs/workflow/` |
| CLI 工具 | 员工发布、wiki 管线、source kit、cognition runtime | `runtime/cognition/` |
| 模块模板 | 六件套骨架、CodeGraph、vendor-extraction-profile | `runtime/cognition/module_scaffold/` |
| 项目模板 | docs/ 七件套、白皮书模板、README 模板、架构说明模板 | `runtime/cognition/project_scaffold/` |
| 发布引擎 | 公司→项目+宿主的统一发布管线 | `runtime/cognition/publish_engine/` |
| 知识管线 | llm-wiki 吸收链、四层 knowledge workspace 定义 | `runtime/cognition/knowledge_workspace.py` |

### 2.2 宿主适配层

**定位**：同一套公司资产在不同宿主中的"翻译层"。每个宿主有独立的适配器。

| 宿主 | agent 发现面 | support 数据面 | prompt 面 |
|------|-------------|---------------|-----------|
| GitHub Copilot | `{project}/.github/agents/` | `{project}/TriCompany-copilot-assets/` | `{project}/.github/prompts/` |
| Claude Code | `{project}/.claude/agents/` | `{project}/TriCompany-claude-assets/` | `{project}/.claude/prompts/` |
| TriMC（未来） | TriMC task-controller register | `{project}/TriCompany-trimc-assets/` | TriMC soul loader |

**关键规则**：
- agent 发现面只放"已上岗的人格 agent + 非人格 registry agent"，不放源侧草稿
- support 数据面只放运行时消费的四层记忆、wiki、audit、workbench
- 同一员工在不同宿主中的 binding 事实由 `TriCompany/.github/binding-profiles/<id>.json` 统一管理，保持跨宿主一致

### 2.3 项目层：TriMetaverse（及未来任何项目）

**定位**：一个具体项目的"应用实例"。公司资产发布到这里，项目特有内容也在这里。

| 类别 | 内容 | 来源 |
|------|------|------|
| 项目身份 | 白皮书、README、project.md | 项目自维护（从公司模板生成） |
| 模块代码 | TriMC、TriSkill、TriAvatar... | 项目自维护 |
| 项目级 registry | business-state、product-state、code-state | 项目自维护 |
| 架构说明 | 三元宇宙架构与模块说明 | 项目自维护（从公司模板生成） |
| 文档治理 | 真源顺序、模块边界、reference 吸收链 | 项目自维护（从公司模板生成） |
| 已上岗 agent | `.github/agents/` | **公司发布** |
| 公司治理规则 | `docs/` 中与公司治理相关的内容 | **公司发布（模板实例化）** |
| 四层记忆 | `TriCompany-copilot-assets/knowledge/` | **公司发布** |

---

## 3. 发布管线：从"硬编码单项目"到"参数化多项目"

### 3.1 当前（有缺陷）

```
TriCompany source ──→ TriMetaverse/TriCompany-copilot-host-assets/
                   ──→ TriMetaverse/.github/agents/
                   ──→ TriMetaverse/docs/（部分）
```

### 3.2 目标架构

```
TriCompany source
    │
    ├── publish --project {project} --host copilot
    │   ├── agents/      → {project}/.github/agents/
    │   ├── prompts/     → {project}/.github/prompts/
    │   ├── support/     → {project}/TriCompany-copilot-assets/
    │   └── governance/  → {project}/docs/（模板实例化）
    │
    ├── publish --project {project} --host claude
    │   ├── agents/      → {project}/.claude/agents/
    │   ├── support/     → {project}/TriCompany-claude-assets/
    │   └── governance/  → {project}/docs/（相同内容，不同格式）
    │
    └── publish --project {project} --host trimc
        ├── agents/      → TriMC task-controller register
        └── support/     → {project}/TriCompany-trimc-assets/
```

### 3.3 关键设计决策

**决策 1：支撑包命名统一为 `TriCompany-{host}-assets/`**

不再有 `TriDev-copilot-host-assets`、`TriSkill-copilot-host-assets` 等按模块拆分的支撑包。TriDev、TriSkill 等工具能力通过 TriCompany 发布引擎统一分发，不需要各自独立发布 support 数据。

**决策 2：knowledge/ 中区分"公司共享"和"项目实例"**

```
TriCompany-{host}-assets/knowledge/
├── org/shared/          # 公司级共享（跨项目一致）
├── audit/               # 审计记录（跨项目汇总或按项目分）
├── roles/               # 角色模板（跨项目一致，公司发布）
└── employees/           # 员工实例（本项目运行态）
```

**决策 3：治理文档走"模板实例化"，不走"全量复制"**

公司级治理规则（如文档治理规则与真源文件系统）以模板形式存在于 TriCompany。发布到具体项目时，根据项目的模块列表、架构表等参数填充实例。项目自维护的项目特有内容（如具体模块边界）不与公司模板混淆。

---

## 4. TriDev → TriCompany 合并方案

### 4.1 合并合理性

- TriDev 的十阶段 phase engine 是赛博公司任何开发型项目的标准流程，属于公司级工具
- TriDev 的模块 scaffold（`NewModuleBaselineRelease` → `TriDev init`）是公司级模块管理工具
- TriDev 的部署 CLI 是公司级部署能力
- 当前"TriDev 作为一个独立模块"造成工具发布和支撑包管理的二重性

### 4.2 合并路径

```
TriDev 当前职责         →  TriCompany 合并后位置
─────────────────────────────────────────────────
十阶段 phase engine      →  runtime/cognition/phase_engine/
模块 scaffold CLI        →  runtime/cognition/module_scaffold/
部署 CLI                 →  runtime/cognition/deploy/
ModuleReadinessInit      →  runtime/cognition/module_readiness/
NewModuleBaselineRelease →  runtime/cognition/new_module_baseline/
```

### 4.3 合并后对外接口

TriCompany 作为公司"操作系统"，对外暴露以下能力接口：

| 接口 | 命令示例 | 用途 |
|------|---------|------|
| 员工入职 | `employee_source_kit generate --employee-id xxx` | 新员工五件套生成 |
| 员工发布 | `employee_host_publish --project xxx --host copilot` | 员工资产发布到项目 |
| 模块初始化 | `module_scaffold init --module-name xxx` | 新模块骨架创建 |
| 项目初始化 | `project_scaffold init --project-name xxx` | 新项目骨架创建 |
| 治理模板发布 | `governance_publish --project xxx` | 公司治理规则发布到项目 |
| Agent 上岗 | `agent_live_enable --employee-id xxx --host copilot` | 将员工 agent 发布到宿主发现面 |
| Wiki 刷新 | `wiki_refresh --employee-id xxx` | 手动触发 LLM wiki 吸收 |

---

## 5. 物理路径对照：当前 vs 目标

### 5.1 公司侧（TriCompany/）

| 资产 | 当前路径 | 目标路径 | 变化 |
|------|---------|---------|------|
| 员工源侧五件套 | `.github/source-agents/<id>/` | `.github/source-agents/<id>/` | 不变 |
| 员工 contract | `docs/registry/<Id>.contract.yaml` | `docs/registry/<Id>.contract.yaml` | 不变 |
| 公司治理状态 | `docs/registry/company-governance-state.md` | `docs/registry/company-governance-state.md` | 不变 |
| 发布流程 | `docs/workflow/host-object-publish-flow.md` | 更新为多项目+多宿主版 | 扩展 |
| Wiki spec | `docs/workflow/chief-of-staff-llm-wiki-object-spec.md` | 不变 | 不变 |
| 认知运行时 | `runtime/cognition/` | `runtime/cognition/` + 合并 TriDev 能力 | 扩展 |
| 项目模板 | 无 | `runtime/cognition/project_scaffold/` | **新增** |
| 治理模板 | 分散在 docs/workflow/ | 统一到 `runtime/cognition/governance_templates/` | **新增** |

### 5.2 项目侧（TriMetaverse/）

| 资产 | 当前路径 | 目标路径 | 变化 |
|------|---------|---------|------|
| Agent 发现面 | `.github/agents/` | `.github/agents/` | 不变（仍由公司发布） |
| Prompt 发现面 | `.github/prompts/` | `.github/prompts/` | 不变 |
| 支撑包 | `TriCompany-copilot-host-assets/` | `TriCompany-copilot-assets/` | **重命名**，去掉 `host` |
| 四层记忆 | `TriCompany-copilot-host-assets/knowledge/` | `TriCompany-copilot-assets/knowledge/` | 路径简化 |
| 项目架构说明 | `docs/三元宇宙架构与模块说明.md` | 不变 | 不变（项目自维护） |
| 文档治理规则 | `docs/文档治理规则与真源文件系统.md` | 不变（项目自维护，从模板实例化） | 不变 |
| 白皮书 | `tmv-whitepaper.md` | 不变 | 不变 |
| 项目 workflow | `project.md` | 不变 | 不变 |
| TriDev 独立仓 | 无（已合并） | 不再需要 | **删除** |

---

## 6. 迁移分期

### Phase 0：概念确认（当前）
- CEO/CPO/CTO 联审本文
- 确认三层模型、TriDev 合并、支撑包命名变更

### Phase 1：公司侧重构
- 合并 TriDev 核心能力到 TriCompany `runtime/cognition/`
- `chief_of_staff_wiki_paths.py` → `employee_wiki_paths.py` 泛化
- 创建项目模板引擎（project_scaffold）
- 创建治理模板引擎（governance_templates）
- 重构 `employee_host_publish` 支持 `--project` 和 `--host` 参数

### Phase 2：TriMetaverse 适配
- 重命名 `TriCompany-copilot-host-assets/` → `TriCompany-copilot-assets/`
- 更新所有 `.github/agents/` 中的路径引用
- 用新发布管线重新发布全部员工

### Phase 3：多宿主验证
- 在 TriMC 练兵场启动后，用 `--host trimc` 发布验证
- 补齐 Claude Code 宿主适配器（`.claude/agents/` 格式）

---

## 7. 决策待定

| # | 决策点 | 选项 | 建议 |
|---|--------|------|------|
| 1 | 支撑包重命名 | `TriCompany-copilot-assets`（去掉 host）vs 保持现状 | 去掉 host，因为 copilot 本身已经是宿主标识 |
| 2 | TriDev 合并时机 | 现在 vs Phase 1 代码泛化完成后 | 先完成代码泛化，再合并 TriDev |
| 3 | knowledge/ 跨项目共享 | org/ 和 roles/ 跨项目共享，employees/ 按项目隔离 vs 全部按项目隔离 | org/ 和 roles/ 共享，employees/ 按项目隔离 |
| 4 | 项目模板引擎优先级 | 立即 vs 等第二个项目启动 | 先做设计、留接口，等第二个项目时实例化 |
| 5 | 治理文档"模板实例化"vs"直接发布" | 复杂的模板引擎 vs 先继续发布完整文档 | 先继续发布完整文档，模板引擎后置 |

---

## 8. 当前不做

- 不立即变更 TriMetaverse 下的物理路径（等 Phase 1 代码泛化完成后再迁）
- 不为尚未存在的第二个项目预建完整模板引擎（先做接口设计）
- 不把 Claude Code / TriMC 宿主适配器写成已完成
- 不改变当前 live agent 发现面的 `.github/agents/` 结构（Phase 2 才动）

---

## 9. 来源

- `TriMetaverse/docs/三元宇宙架构与模块说明.md`（项目级架构面）
- `TriCompany/docs/workflow/host-object-publish-flow.md`（当前发布流程）
- `TriCompany/docs/registry/company-governance-state.md`（公司治理状态）
- `TriMetaverse/project.md`（项目 workflow）
- `TriMetaverse/docs/文档治理规则与真源文件系统.md`（项目级文档治理）
- 当前 CEO 意见（本次会话）
