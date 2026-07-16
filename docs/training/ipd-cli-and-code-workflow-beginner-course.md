# IPD CLI 与代码工作流程教程（小白版）

版本：V0.3

日期：2026-07-09

状态：渐进式教程真源（诚实化：标注 [planned] 功能，更新命令表与实际 CLI 一致）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/training/ipd-cli-and-code-workflow-beginner-course.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/training/ipd-cli-and-code-workflow-beginner-course.md
- supportSyncRule: IPD runtime engine（ipd_case_engine.py）或 CLI（chief_of_staff_ipd_case.py）发生稳定语义变更后，本教程应在同轮或下一轮追平
- lastSyncedAt: 2026-07-09
- lastSyncedCommit: 9793ee8e

## 0. 教学定位

这份教程由 `RAndDTrainer`（小吴）面向技术研发新人维护，用来把 IPD 的 CLI 启动、代码执行链、搜索 / CodeGraph 调用边界、每个流程节点的输入输出讲清楚。

本教程是 `TriCompany` 模块内的 training 真源，不替代以下真源：

1. 流程真源：[../workflow/integrated-product-development-flow.md](../workflow/integrated-product-development-flow.md)
2. 运行时代码：`TriCompany-copilot-host-assets/runtime/cognition/chief_of_staff_ipd_case.py`
3. IPD case engine：`TriCompany-copilot-host-assets/runtime/cognition/ipd_case_engine.py`

当前目标分两条线同步推进：

1. IPD 全流程继续完善：当前按 `IPD-20260612-WORKFLOW-002` 这条 `process-improvement + WORKFLOW` 优化线修流程，再用 `IPD-20260610-PLATFORM-001` 这条 full-scope `project-delivery + PLATFORM` case 做受控 replay / 产品主线消费；`IPD-20260611-PLATFORM-001` 只作为已完成 `ceo-demand -> delivery` 全链路 proving-ground replay 的证据基线。
2. IPD 教程同步完成：流程每改稳一段，本教程就补齐对应讲解，保证未来培训学院可复用。

## 1. 一句话先看懂 IPD CLI 在干什么

你在 `TriMetaverse` 根目录输入：

```powershell
.\tmv.cmd dev-task "做一个完整模型 API 平台 MVP"
```

它不是直接写代码。它会先把这句话变成一条 `TriCompany IPD case`，再让 runtime 判断：

1. 这个任务信息够不够进入正式 IPD。
2. 当前应该停在 CEO 补槽、总助分派、CPO / CTO owner action，还是继续自动签核。
3. 如果进入开发型项目线，是否需要桥接 `TriDev` 的十阶段 phase engine。

把它想成三层：

| 层 | 负责什么 | 主要文件 |
| --- | --- | --- |
| CLI 外壳 | 把用户命令转成 PowerShell / Python 调用 | `TriMetaverse/tmv.cmd`、`TriMetaverse/tmv.ps1`、`TriMetaverse/scripts/dev-task.ps1` |
| TriCompany IPD runtime | 管 case、intake、阶段、签核、暂停、证据门禁 | `TriCompany-copilot-host-assets/runtime/cognition/chief_of_staff_ipd_case.py`、`TriCompany-copilot-host-assets/runtime/cognition/ipd_case_engine.py` |

## 2. CLI 启动链路

### 2.1 第 1 跳：`tmv.cmd`

入口：

```powershell
.\tmv.cmd dev-task "任务描述"
```

代码位置：`TriMetaverse/tmv.cmd`

它只做一件事：用 PowerShell 运行 `tmv.ps1`。

输入：

- `dev-task`
- 后面的任务描述和参数

输出：

- 把参数原样交给 `tmv.ps1`
- 返回 `tmv.ps1` 的退出码

### 2.2 第 2 跳：`tmv.ps1`

代码位置：`TriMetaverse/tmv.ps1`

它识别 `dev-task` 命令，然后调用：

```powershell
scripts\dev-task.ps1
```

输入：

- `Command = dev-task`
- `Arguments = <任务描述和选项>`

输出：

- 如果命令是 `dev-task`：继续执行 `scripts\dev-task.ps1`
- 如果命令为空：打印帮助
- 如果命令未知：报错 `Unknown tmv command`

### 2.3 第 3 跳：`scripts/dev-task.ps1`

代码位置：`TriMetaverse/scripts/dev-task.ps1`

这是稳定 CLI alias 的核心脚本。它会：

1. 收集参数：`--workspace-root`、`--tridev-root`、`--intake-only`、`--manual-ceo-signoff` 等。
2. 把剩余文本拼成 `taskDescription`。
3. 找到同级源仓：`D:\OneDrive\Code\ai\TriCompany`。
4. `Push-Location` 到 `TriCompany`。
5. 先运行 `task-intake`。
6. 如果不是 `--intake-only`，运行后续流程（autopilot [planned]：当前引擎无 autopilot 功能，实际为人工推进）。
7. 把 intake 和后续结果的 JSON 合并成最终 JSON 输出。

关键 Python 调用是：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case task-intake "任务描述"
# autopilot [planned]：当前 CLI 无此子命令，实际需手动 intake-approve / submit / signoff 逐步推进
```

输入：

- 用户任务描述
- 可选的 workspace / TriDev root / 自动签核策略

输出：

- `caseId`
- `intake` JSON
- `[planned]` autopilot JSON（当前 CLI 无 autopilot 功能）

常用变体：

```powershell
.\tmv.cmd dev-task --intake-only "只创建 case，不继续执行后续流程（[planned] autopilot）"
.\tmv.cmd dev-task --manual-ceo-signoff "创建 case，并在 CEO 签核点暂停（[planned] autopilot）"
.\tmv.cmd dev-task --tridev-root D:\OneDrive\Code\ai\TriDev "显式指定 TriDev 源仓（[planned] TriDev bridge）"
```

## 3. Python CLI 入口怎么分发命令

代码位置：`TriCompany-copilot-host-assets/runtime/cognition/chief_of_staff_ipd_case.py`

这个文件使用 `argparse` 定义 IPD 子命令。你可以把它理解为 IPD runtime 的命令总路由。

**当前可用命令（7 个）：**

| 子命令 | 函数 | 作用 |
| --- | --- | --- |
| `task-intake` | `initialize_ipd_case(...)` | 把一句任务变成 IPD case 和 intake brief |
| `init` | `initialize_ipd_case(...)` | 精调 / 补齐 intake 字段 |
| `intake-approve` | `record_intake_signoff(...)` | 记录 CEO / 总助的 intake 签核 |
| `submit` | `submit_stage_output(...)` | 阶段 owner 提交阶段产物 |
| `signoff` | `record_stage_signoff(...)` | CEO / 总助对阶段产物签核 |
| `status` | `read_ipd_case(...)` | 读取 case 当前状态 |
| `step` | `reconcile_ipd_case(...)` | 让 runtime 按当前状态重算能否推进 |

**`[planned]` 设计目标命令（当前不可用）：**

| 子命令 | 设计目标函数 | 作用 |
| --- | --- | --- |
| `discovery` | `run_discovery_stage_automation(...)` | 自动生成 Discovery reference package |
| `intelligence` | `run_intelligence_stage_automation(...)` | 自动生成 Intelligence code/reference package |
| `rollback` | `rollback_ipd_case(...)` | 回退到 `ceo-demand`、`task-dispatch` 或某个 stage |
| `freeze` / `unfreeze` | `freeze_ipd_case(...)` / `unfreeze_ipd_case(...)` | 条件性冻结或恢复 |
| `autopilot` | `run_case_autopilot(...)` | 自动推进可自动处理的节点 |

## 4. 从一条任务到 case：`task-intake`

### 4.1 输入

最小输入是一句任务：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case task-intake "做一个完整模型 API 平台 MVP"
```

也可以显式补字段：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case task-intake `
  --case-id IPD-20260629-PLATFORM-001 `
  --case-category project-delivery `
  --reference-theme PLATFORM `
  --slot-answer "competitorReference=OpenAI API Platform、OpenRouter、One API" `
  --slot-answer "targetUserScenario=内部产品和技术负责人验证统一模型 API 入口" `
  --slot-answer "deliveryWindow=1 周内完成 Discovery 与 Intelligence" `
  --slot-answer "budgetGuardrail=只用现有人力和少量工具试验成本" `
  --slot-answer "successMetric=自动形成 discovery / intelligence markdown package" `
  --slot-answer "mustHaveScope=完成首轮 package 与可提交 stage output" `
  --slot-answer "explicitOutOfScope=不涉及 TriMC 服务器正式版上线" `
  "做一个完整模型 API 平台 MVP"
```

### 4.2 代码执行

`chief_of_staff_ipd_case.py` 会做这些事：

1. `_normalize_task_text(...)`：把多段参数合并成一段任务描述。
2. `_generate_case_id(...)`：如果没传 `--case-id`，自动生成 `IPD-YYYYMMDD-主题-序号`。
3. `_derive_title(...)` / `_derive_objective(...)`：从任务描述推导标题和目标。
4. `_resolve_related_modules(...)`：推断相关模块。
5. `initialize_ipd_case(...)`：创建 case、intake、阶段模板和 clarification sheet。

### 4.3 输出

运行态对象默认写到 support workbench，而不是写进 TriCompany 源仓：

```text
TriMetaverse\TriCompany-copilot-host-assets\knowledge\employees\ceo-chief-of-staff\workbench\ipd\cases\<case-id>\
```

关键文件：

| 文件 | 作用 |
| --- | --- |
| `case.json` | case 主状态 |
| `intake-brief.json` | intake briefing、clarification sheet、签核信息 |
| `events.jsonl` | 事件流水 |
| `work-items\*.json` | 每个阶段激活时生成的工作单 |
| `outputs\*.json` | 阶段提交后的产物包 |

### 4.4 最常见暂停

如果关键槽位不完整，系统会停在 `paused-intake-clarification`（[planned] autopilot 功能；当前为人工判断暂停点）：

```text
paused-intake-clarification
```

这不是失败，而是提醒 CEO / 总助先补齐：

- 竞品 / 对标对象
- 目标用户与场景
- 工期
- 预算护栏
- 成功信号
- 必须交付范围
- 明确不做项

## 5. 模块路由：这里是否调用搜索工具？

`task-intake` 会推断 `relatedModules`，但默认不做网页搜索。

它有三种路由模式：

| 模式 | 行为 | 是否外部调用 |
| --- | --- | --- |
| `deterministic` | 用本地关键词规则匹配模块，例如模型 API -> `TriStaciss`，Web 前端 -> `TriAvatar` | 否 |
| `cpo` | 调用环境变量 `TRICOMPANY_CPO_MODULE_ROUTER_COMMAND` 指向的 CPO router | 是，`subprocess.run(..., shell=True)` |
| `auto` | 如果 CPO router 已配置就先调用；没配置就回退 deterministic | 可能 |

当前稳定 CLI 默认是 `auto`。如果没有设置 `TRICOMPANY_CPO_MODULE_ROUTER_COMMAND`，就不会调用外部 CPO router，也不会调用搜索工具。

如果 CPO router 返回 `needsBusinessStrategyEscalation=true`，runtime 会直接报错并要求升级 `BusinessStrategy`，不会静默回退。

## 6. intake 签核：从入口 briefing 到第一阶段 work item

### 6.1 输入

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id <case-id> `
  --role CEO `
  --decision approved

python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id <case-id> `
  --role CEOChiefOfStaff `
  --decision approved
```

### 6.2 代码执行

`record_intake_signoff(...)` 会：

1. 读取 `case.json`。
2. 计算 intake package hash。
3. 记录 web3-simulated 签名信息。
4. 当 `CEOChiefOfStaff` 最终签核且 approvals 全部通过时，签发 intake release version。
5. 调用 `reconcile_ipd_case(...)`。

### 6.3 输出

成功后，case 通常进入：

```text
waiting-stage-output
```

并激活第一阶段，比如 `discovery` 或流程优化线的 `backlog`。runtime 会写出：

```text
work-items\01-discovery.json
```

`entryCheckpoint` 通常会从 `ceo-demand` 变成 `task-dispatch` 或正式 stage key。

## 7. Discovery（[planned]：当前 CLI 无 `discovery` 子命令，引擎无自动化函数）

> 以下为设计目标，当前 Discovery 产出由人工（CPO/CTO）手动完成。

### 7.1 [planned] 输入

Discovery 的直接输入是：

- 总助拆解后的研发任务说明
- `intake-brief.json`
- 关键槽位答案
- 当前阶段边界

命令（[planned]）：

```powershell
# [planned] 未来命令：
python -m runtime.cognition.chief_of_staff_ipd_case discovery `
  --case-id <case-id> `
  --submit
```

### 7.2 是否调用搜索工具？

流程真源要求 CPO 做“全网搜索符合情况的产品和官方手册”。但当前 `run_discovery_stage_automation(...)` 的实现不是实时打开浏览器或搜索引擎。

当前代码实际做的是：

1. 基于 case 槽位和内置 `_DISCOVERY_SOURCE_SEEDS` 生成 seeded source catalog。
2. 把来源登记为 `captureMode = seeded-auto-generated`。
3. 自动写出 Discovery markdown package 草稿。
4. 要求 CPO / 人工后续补充真实抓取、离线快照或额外官方来源。

所以小白要记住：

```text
Discovery automation 现在会生成可复核的研究包草稿，但不等于已经完成真实网页搜索和材料下载。
```

### 7.3 输出

输出目录：

```text
TriMetaverse\reference\discovery\<case-id>\
```

关键文件：

| 文件 | 输出内容 |
| --- | --- |
| `reference-source-catalog.json` | 对标产品 / 官方资料来源目录 |
| `discovery-reference-functional-brief.md` | 功能简报 |
| `discovery-competitor-landscape.md` | 竞品地图 |
| `discovery-common-capability-matrix.md` | 共性能力矩阵 |
| `discovery-highlight-opportunity-memo.md` | 亮点机会备忘录 |

如果带 `--submit`，runtime 还会把这些文件作为 evidence 调用 `submit_stage_output(...)` 提交 Discovery 阶段。

## 8. Intelligence：开源代码 reference、CodeGraph 与 PRD 输入

### 8.1 输入

Intelligence 的直接输入是：

- Discovery package
- `DiscoveryReferenceFunctionalBrief`
- 市场 / 运营 / 财务 / 产品约束
- 相关开源或公开资料锚点

命令：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intelligence `
  --case-id <case-id> `
  --submit
```

如果不想尝试 CodeGraph：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intelligence `
  --case-id <case-id> `
  --submit `
  --no-codegraph
```

### 8.2 是否调用搜索工具？

当前 Intelligence automation 也不是实时网页搜索或 git clone。

它实际做的是：

1. 根据 Discovery 输入和 `_INTELLIGENCE_SOURCE_SEEDS` 生成开源 / 公开资料来源目录。
2. 对带 `localPath` 的来源，尝试调用本机 `codegraph`。
3. 如果 `codegraph` 不存在，记录 `codegraph command not available`，并把 CodeGraph 状态降级为待执行或失败说明。
4. 写出 Intelligence markdown package。

这里可能发生的外部命令调用只有 CodeGraph：

```text
codegraph status <project>
codegraph init -i <project>
codegraph context -p <project> "<task>"
```

它通过 Python `subprocess.run(...)` 调用，超时时间 600 秒。

### 8.3 输出

输出目录：

```text
TriMetaverse\reference\intelligence\<case-id>\
```

关键文件：

| 文件 | 输出内容 |
| --- | --- |
| `reference-source-catalog.json` | 开源 / 公开资料来源目录 |
| `intelligence-capability-extraction-matrix.md` | 能力提取矩阵 |
| `intelligence-opensource-landscape.md` | 开源地图 |
| `intelligence-codegraph-analysis.md` | CodeGraph 深读记录 |
| `intelligence-architecture-option-memo.md` | 架构选型备忘录 |

这些输出的目标不是直接替代 PRD，而是给 CPO 写正式 PRD 提供结构化输入。

## 9. Autopilot（[planned]：当前引擎和 CLI 无此功能）

> 以下为设计目标——`run_case_autopilot(...)` 在当前 `ipd_case_engine.py` 中不存在，CLI 无 `autopilot` 子命令。当前阶段所有步骤需人工手动推进。

### 9.1 [planned] 它会自动做的事

| 状态 | 自动动作 |
| --- | --- |
| `awaiting-intake-approvals` | 如果待签角色在 auto approve 列表里，自动签 intake |
| `waiting-stage-output` | 对无需 owner action / 真实工程证据的阶段，生成 participant record 和 autopilot package 并提交 |
| `awaiting-stage-approvals` | 如果待签角色在 auto approve 列表里，自动签阶段 |
| 其他可 reconcile 状态 | 调用 `reconcile_ipd_case(...)` 重算推进 |

### 9.2 [planned] 它会暂停的情况

| 暂停状态 | 代表什么 |
| --- | --- |
| `paused-intake-clarification` | CEO / 总助还要补槽 |
| `paused-frozen` | 有岗位基于专业判断冻结 |
| `paused-manual-approval` | 某个签核角色不在自动签核列表，例如 `--manual-ceo-signoff` |
| `paused-owner-action` | CPO / CTO / 总助 owner action 需要真人提交真实阶段产物 |
| `paused-real-execution` | `coding` 到 `delivery` 需要源码、测试、部署或运行证据 |

### 9.3 [planned] 为什么 CPO / CTO 阶段常会暂停

当前 runtime 明确规定：autopilot 不再代表 `ChiefProductOfficer` 或 `ChiefTechnologyOfficer` 直接提交阶段输出。

如果当前阶段 acting owner 是：

- `CEOChiefOfStaff`
- `ChiefProductOfficer`
- `ChiefTechnologyOfficer`

autopilot 会先生成 owner action package，然后停下等待真实 owner 提交。

这样做是为了避免“文档自动生成了”被误认为“产品 / 技术判断已经真实完成”。

## 10. Coding 到 Delivery：为什么需要真实工程证据

从以下阶段开始，runtime 要求真实工程执行证据：

```text
coding
verify-integration
redteam
qa
deployment
assurance
delivery
```

代码判断逻辑在：

```text
TriCompany-copilot-host-assets/runtime/cognition/ipd_case_engine.py
_stage_requires_real_execution(...)
_validate_stage_submission_evidence(...)
```

证据不能只来自：

- `docs/`
- `knowledge/`
- `workbench/`
- `participant-records/`
- `autopilot-packages/`
- `phase-results/`
- 纯 `.md` 文档

它至少要包含真实 source / test / deploy / runtime evidence，例如：

- 源码文件改动
- 测试代码或测试结果
- 部署配置或部署输出
- 运行日志或接口调用结果
- 非 docs/workbench 生成物的制品

所以小白要记住：

```text
IPD 不是靠文档自动跑完。Coding 之后必须有真实工程证据。
```

## 11. TriDev bridge（[planned]：当前引擎和 CLI 无此集成）

> 以下为设计目标——当前 `ipd_case_engine.py` 不调用 TriDev workflow，CLI 无 TriDev bridge 功能。开发型项目当前需人工手动推进。

当 autopilot 启用 TriDev bridge 时（[planned]），`run_case_autopilot(...)` 会：

1. 找到 `TriDev` 源仓。
2. 动态导入 `TriDev/src/tridev/workflow.py`。
3. 确保存在对应 run：`ipd-<case-id-lowercase>`。
4. 对每个可自动提交的阶段，写一份 TriDev stage artifact。
5. 调用 `record_phase_result(...)` 写 phase result。
6. 调用 `record_gate(...)` 写 gate ledger。
7. 到 `DELIVERY` 时生成 delivery manifest、release bundle，并校验 bundle。

TriDev 输出目录通常是：

```text
TriMetaverse\TriDev-copilot-host-assets\docs\runs\ipd-<case-id-lowercase>\
```

关键文件：

| 文件 | 作用 |
| --- | --- |
| `run-metadata.json` | run 主状态 |
| `workflow-state.json` | 当前 phase 状态 |
| `phase-results\*.json` | 每阶段结果 |
| `gate-ledger.json` | gate 放行记录 |
| `artifact-bindings.json` | artifact digest 和变更证据 |
| `knowledge-bundle.json` | 给宿主 / 执行器的知识包 |
| `host-prompt-context.json` | 给宿主的 prompt context |
| `coding-task-plan.json` | 编码任务计划 |
| `artifacts\release.zip` | delivery 阶段 release bundle |

当前边界：

```text
TriDev 已有最小 run / gate / evidence 执行层，但完整岗位 adapter、PRD 分叉并行、多分支 delivery 聚合仍待继续补齐。
```

## 12. 每个主流程节点的输入 / 输出速查

| 节点 | 输入 | 输出 | 主要状态 |
| --- | --- | --- | --- |
| `task-intake` | 任务描述、可选 case id、slot answers、模块路由模式 | `case.json`、`intake-brief.json`、`clarificationSheet` | `paused-intake-clarification` 或 `awaiting-intake-approvals` |
| `intake-approve: CEO` | intake package hash、CEO decision | CEO signature | 仍等待总助签核 |
| `intake-approve: CEOChiefOfStaff` | CEO 已签的 intake、总助 decision | intake release version、首阶段 work item | `waiting-stage-output` |
| `submit` | 阶段 owner、summary、details、evidence、object path | `outputs\NN-stage.json`、owner signature | `awaiting-stage-approvals` |
| `signoff: CEO` | stage package hash、CEO decision | CEO stage signature | 等待总助终签 |
| `signoff: CEOChiefOfStaff` | 已签 stage package、总助 decision | stage release version、下一阶段 work item | 下一阶段 `waiting-stage-output` 或 `completed` |
| `step` | case id | 重算当前状态、推进到下一阶段 | 不变或下一等待状态 |

**`[planned]` 节点速查（当前不可用）：**

| 节点 | 设计目标 |
| --- | --- |
| `discovery` | Discovery 五件套自动生成、可选 stage output |
| `intelligence` | Intelligence 五件套自动生成、可选 CodeGraph |
| `autopilot` | 自动推进至人工或真实证据门前暂停 |
| `rollback` | 回退到指定 checkpoint / stage |
| `freeze` / `unfreeze` | 冻结 / 解冻角色与原因 | freezeControl 或恢复状态 | `paused-frozen` / 原流程继续 |

## 13. 小白调试时先看什么

按这个顺序排查：

1. 先看命令输出里的 `caseId`。
2. 再跑 `status` 看 `status`、`entryCheckpoint`、`currentStageKey`、`currentOwnerRole`。
3. 如果是 `paused-intake-clarification`，看 `missingSlotKeys` 和 `followUpQuestions`。
4. 如果是 `paused-owner-action`，看 `ownerActionPackageRef`。
5. 如果是 `paused-real-execution`，补真实源码 / 测试 / 部署 / 运行证据。
6. 如果 Discovery / Intelligence 文件生成了，不要只看文件存在，要看正文是否有真实内容和边界。
7. 如果 CodeGraph 没跑起来，看 Intelligence catalog 里的 `codegraph.status` 和 `statusOutput`。
8. 如果 TriDev bridge 失败，看 `TriDev` 源仓是否存在，以及 `TriDev/src/tridev/workflow.py` 是否可导入。

## 14. 分段讲解建议

未来培训学院可以把本教程拆成五段课：

| 课段 | 目标 | 学员能复述的结果 |
| --- | --- | --- |
| 第 1 段：CLI 外壳 | 看懂 `tmv.cmd -> tmv.ps1 -> dev-task.ps1` | 知道命令从 TriMetaverse 切到 TriCompany |
| 第 2 段：case 状态机 | 看懂 `case.json`、`intake-brief.json`、`entryCheckpoint` | 能判断 case 卡在哪 |
| 第 3 段：Discovery / Intelligence | 看懂 reference package 和 CodeGraph 边界 | 知道哪些是自动草稿，哪些需要人工补证 |
| 第 4 段：Autopilot / TriDev bridge | 看懂自动签核、owner action、phase result 和 gate | 知道自动化不会替代 CPO / CTO 判断 |
| 第 5 段：Coding 之后的真实证据 | 看懂为什么 docs 不等于交付 | 能准备源码、测试、部署和运行证据 |

## 15. 渐进式维护规则

本教程不是一次性完成后冻结。后续 IPD 每优化一段，都按这个规则更新：

1. 先确认流程或代码已经在 `WORKFLOW-*` 优化线完成。
2. 再确认 `IPD-20260610-PLATFORM-001` 的受控 replay / 产品主线消费通过；若引用 `IPD-20260611-PLATFORM-001`，只能把它写成已完成全链路 replay 的证据基线。
3. 然后更新本教程对应段落。
4. 如果更新涉及产品判断，交 CPO 复核。
5. 如果更新涉及 runtime、TriDev bridge、测试、部署或证据门禁，交 CTO 复核。
6. 如果 `integrated-product-development-flow.md`、`platform-product-mainline-cutover.md`、`ipd-company-baseline-checklist.md` 或 `IPD-20260612-WORKFLOW-002` 改变 case 分工、Gate A/B/C 目标或 replay 口径，必须把本教程列入同轮检查清单；这次漏同步的原因，就是教程是 `source-only` training 真源，没有 active published-copy manifest 自动触发，且旧 `supportSyncRule` 只写了 runtime / stage contract，没有显式覆盖 case 分工与验证目标。
7. 如果更新涉及 training 发布位置，交 CEOChiefOfStaff 收口。
8. 未来 TriTraining 模块成熟后，再把稳定版本发布为培训学院课程包。

## 16. 当前未完成 / 待继续优化

当前仍不能写成已完成的能力：

1. 实时网页搜索 / 浏览器采集没有由 IPD CLI 自动完成；当前 Discovery / Intelligence 主要是 seeded package 与人工补证。
2. 完整岗位 adapter 尚未完成。
3. PRD 分叉并行与多分支 delivery 聚合尚未完成。
4. TriMC 服务器正式版上线尚未完成。
5. 培训学院产品化发布尚未完成。

## 17. 真源回链

- [IPD 使用教程](ipd-usage-guide.md)
- [从 CEO Demand 到 Discovery 的产品与代码教程（小白版）](ceo-demand-to-discovery-beginner-course.md)
- [集成产品开发流程（IPD 流程）](../workflow/integrated-product-development-flow.md)
- [完整模型 API 平台产品主链切换说明](../workflow/platform-product-mainline-cutover.md)
- `TriMetaverse/tmv.cmd`
- `TriMetaverse/tmv.ps1`
- `TriMetaverse/scripts/dev-task.ps1`
- `TriCompany/runtime/cognition/chief_of_staff_ipd_case.py`
- `TriCompany/runtime/cognition/ipd_case_engine.py`
- `TriCompany/runtime/cognition/chief_of_staff_wiki_paths.py`
- `TriDev/src/tridev/workflow.py`

## 18. 变更记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-06-29 | V0.1 | 根据 `CARRY-20260629-006` 新增独立教程，补齐 CLI 启动链、代码执行链、搜索 / CodeGraph 调用边界、节点输入输出和渐进式维护规则。 |
