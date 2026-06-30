# IPD 使用教程（面向 RAndDTrainer 与技术研发新人）

版本：V0.3

日期：2026-06-29

状态：当前 Copilot-host live 阶段可用的最小教程

## 1. 教程范围

这份教程只讲当前 TriCompany 边界里已经可运行的最小 IPD 闭环：如何把一条来自 CEO / CEOChiefOfStaff 的事项，推进成可由各岗位继续细化、提交、签核和放行的工作链。

它不讲 TriMC 正式宿主，也不讲完整自动化公司，更不把某个具体项目的 Discovery / Intelligence 资料当成流程教程本身。

当前教程覆盖的最小闭环是：

- `task-intake -> init -> intake-approve`
- 流程优化线：`backlog -> sprint-planning -> sprint-execution -> sprint-review -> retrospective -> validation-handoff`
- 项目验证线：`discovery -> intelligence -> designing -> coding -> verify-integration -> redteam -> qa -> deployment -> assurance -> delivery`
- intake `CEO signoff -> CEOChiefOfStaff verify -> release`
- 每阶段 `submit(owner 自动签 package hash) -> signoff(CEO) -> signoff(CEOChiefOfStaff) -> release`
- `status`、`step`、`rollback`
- `entryCheckpoint` 对入口节点的显式表达
- web3-simulated 签核与 autopilot 自动签核 / 人工暂停语义

当流程已经进入“长期 contract 联审与第一次真实审批回填”阶段时，培训应追加阅读 [../workflow/ipd-first-real-approval-backfill-runbook.md](../workflow/ipd-first-real-approval-backfill-runbook.md)，不要把审批演练、真实审批回填、主流程 merge hook 回写和 runtime 双写继续留在口头说明层。

如果培训对象需要先理解 `.\tmv.cmd dev-task` 如何启动、PowerShell 如何切到 TriCompany、Python runtime 如何分发命令、Discovery / Intelligence 是否真的调用搜索工具、TriDev bridge 如何写 run / gate / evidence，请先读独立教程：[IPD CLI 与代码工作流程教程（小白版）](ipd-cli-and-code-workflow-beginner-course.md)。

## 2. 先分清两类 case

### 2.1 `process-improvement`

这类 case 用来完善 IPD 流程自身，例如：

- intake 补槽
- 总助 dispatch
- rollback 到 `ceo-demand` / `task-dispatch`
- Discovery / Intelligence 自动化
- autopilot pause summary
- 训练教程、演示 case、host 接口适配

这类 case 默认应该使用：

- `caseCategory=process-improvement`
- `referenceTheme=WORKFLOW`

### 2.2 `project-delivery`

这类 case 用来使用已经固化的 IPD 流程去开发具体项目，例如模型 API 中转平台。

这类 case 的：

- CEO 需求
- 竞品名单
- Discovery reference
- Intelligence 开源代码
- PRD / 设计 / 交付资料

都只服务该项目本身，不再反向充当 IPD 流程教程。

这类 case 通常使用：

- `caseCategory=project-delivery`
- `referenceTheme=PLATFORM` 或其他项目主题

### 2.3 当前教程默认走哪条线

本教程默认先讲第一类，也就是先把 IPD 流程本身跑顺、跑稳、讲清楚；这条线现在走的是 `agile-improvement`，不是再拿 IPD 十阶段自己套自己。

等流程阶段性优化完，再另开独立 `project-delivery` case，从 `ceo-demand` 重新开始，实际验证 Discovery / Intelligence / PRD / 交付链。

## 3. 当前 runtime 怎样对齐两条执行线

当前 runtime 里有两条 canonical execution line：

- 流程优化 case：`BACKLOG -> SPRINT-PLANNING -> SPRINT-EXECUTION -> SPRINT-REVIEW -> RETROSPECTIVE -> VALIDATION-HANDOFF`
- 项目交付 case：`DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY`

TriCompany 的 IPD runtime 不是把所有事项都硬塞进同一条阶段线，而是把：

- 哪个岗位接单
- 哪个岗位提交资料
- 哪个岗位有冻结权
- 总助 / CEO 如何签核放行

挂到和 case 类型匹配的执行线上。

当前 live 阶段的最小入口节点有三类：

- `ceo-demand`：还在 CEO 提需求 / intake 澄清层
- `task-dispatch`：总助已完成分派，但当前 flow 的首阶段 owner 还没开始正式提交
- 正式 stage key：流程优化线例如 `backlog`、`sprint-planning`；项目交付线例如 `discovery`、`intelligence`、`designing`

因此培训时要优先看 `entryCheckpoint`，不要再只靠 `status + currentStageKey` 自己猜入口位置。

## 4. 命名与显式字段

### 4.1 case id

当前建议统一使用日期前置的命名：

- `IPD-YYYYMMDD-文字简称-序号`
- 例如：`IPD-20260612-WORKFLOW-002`、`IPD-20260610-PLATFORM-001`

本教程使用 `IPD-20260612-WORKFLOW-002` 作为当前流程优化示例 id，使用 `IPD-20260610-PLATFORM-001` 作为当前项目验证 / 产品主线示例 id；`IPD-20260611-PLATFORM-001` 仅作为已完成全链路 proving-ground replay 的证据基线说明。

### 4.2 显式分类字段

从当前版本开始，初始化 case 时可以显式写出：

- `--case-category`
- `--reference-theme`

推荐搭配：

- 流程完善：`process-improvement + WORKFLOW`
- 项目交付：`project-delivery + PLATFORM`

这样 Discovery / Intelligence 的 source 选择不再依赖 case id 的短名去“猜”你想做的是流程研发还是项目研发。

## 5. 启动一条最小流程完善 case

### 5.1 第一步：先用 `task-intake` 接住 CEO / 总助的粗任务

当上游只有一句总要求时，先不要要求 CEO 一次性把所有字段写完，先把事项落成 case：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case task-intake `
  --case-id IPD-20260611-WORKFLOW-001 `
  --case-category process-improvement `
  --reference-theme WORKFLOW `
  "完善公司级 IPD 流程，使 CEO 提需求、总助补槽分派、Discovery 和 Intelligence 自动化能够稳定复用"
```

这一步会先生成：

- `case.json`
- `intake-brief.json`
- 初始 `clarificationSheet`

### 5.2 第二步：再用 `init` 把 intake briefing 精调成可签版

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case init `
  --case-id IPD-20260611-WORKFLOW-001 `
  --title "IPD 流程完善最小闭环" `
  --objective "先把 IPD intake、dispatch、签核链、rollback 和敏捷流程优化固化为稳定流程。" `
  --task-description "本轮先完善 IPD 流程自身，不在这条 case 里直接开发具体业务项目。" `
  --case-category process-improvement `
  --reference-theme WORKFLOW `
  --slot-answer "competitorReference=Cursor、Devin、Linear" `
  --slot-answer "targetUserScenario=先服务 CEOChiefOfStaff 与产品/技术负责人，验证公司级研发任务分派场景" `
  --slot-answer "deliveryWindow=先在 1 周内完成 backlog、sprint-planning、sprint-execution 的流程回填验证" `
  --slot-answer "budgetGuardrail=首轮仅使用现有人力和少量工具试验成本" `
  --slot-answer "successMetric=证明流程优化 case 能按 agile 阶段稳定承接 CEO demand、补槽、分派和签核" `
  --slot-answer "mustHaveScope=首轮必须交付 intake briefing、agile backlog/sprint package、入口节点与回滚语义" `
  --slot-answer "explicitOutOfScope=不在本 case 内直接开发模型 API 中转平台、不涉及正式宿主切换" `
  --related-module TriCompany `
  --related-module TriDev
```

### 5.3 第三步：做 intake 核签

当前 intake 的 canonical 顺序已经改为：`CEO` 先对 intake package hash 签名，`CEOChiefOfStaff` 最后验证 CEO 签名并签发正式 intake 版本。

如果使用 autopilot：

- 默认自动签核仍然有效；runtime 会为自动批准岗位生成 deterministic simulated wallet 完成签名。
- 如果希望保留 CEO 人工签核点，可通过 `--manual-ceo-signoff` 或限制 `auto_approve_roles` 让 autopilot 暂停。

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id IPD-20260611-WORKFLOW-001 `
  --role CEO `
  --decision approved `
  --mnemonic "<twelve-or-twenty-four-words>"

python -m runtime.cognition.chief_of_staff_ipd_case intake-approve `
  --case-id IPD-20260611-WORKFLOW-001 `
  --role CEOChiefOfStaff `
  --decision approved `
  --signing-key <web3-private-key>
```

通过后，`process-improvement + WORKFLOW` case 会进入 `backlog`，`entryCheckpoint` 会显示为 `task-dispatch`，表示总助已经完成分派、backlog owner 待开始接单。

### 5.4 第四步：随时用 `status` 看当前位置

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case status `
  --case-id IPD-20260611-WORKFLOW-001
```

培训时至少要让新人看懂这几个字段：

- `status`
- `entryCheckpoint`
- `caseCategory`
- `referenceTheme`
- `currentStageKey`
- `currentOwnerRole`
- `completedStageCount`
- `stageCount`

## 6. 用独立 project-delivery case 做分段能力验证

流程优化 case 走 agile-improvement；只有当流程已经阶段性固化后，才另开独立 `project-delivery` case 去验证真实项目能力。

当前建议固定一个 project-delivery case 做受控 replay / 产品主线消费，不再每轮新造一个临时项目 case。现阶段 Gate A / Gate B / Gate C 的继续验证目标对齐 `IPD-20260610-PLATFORM-001`；`IPD-20260611-PLATFORM-001` 已完成 `ceo-demand -> delivery` 全链路 replay，不再作为待补跑的默认 proving-ground。

### 6.1 Discovery

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case discovery `
  --case-id IPD-20260610-PLATFORM-001 `
  --submit
```

当前会自动生成并刷新：

- `DiscoveryReferenceFunctionalBrief`
- `DiscoveryCompetitorLandscape`
- `DiscoveryCommonCapabilityMatrix`
- `DiscoveryHighlightOpportunityMemo`

输出目录在：

- `TriMetaverse/reference/discovery/<case-id>/`

### 6.2 Intelligence

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case intelligence `
  --case-id IPD-20260610-PLATFORM-001 `
  --submit
```

当前会自动生成并刷新：

- `IntelligenceCapabilityExtractionMatrix`
- `IntelligenceOpenSourceLandscape`
- `IntelligenceCodegraphAnalysis`
- `IntelligenceArchitectureOptionMemo`

输出目录在：

- `TriMetaverse/reference/intelligence/<case-id>/`

### 6.3 当前这两步为什么重要

对独立项目验证 case 来说，这两步验证的是：

- Discovery 输入能不能从补槽稳定落到研究包
- Intelligence 输入能不能从 Discovery 稳定进入代码研究包
- source 选择是否受 `caseCategory` / `referenceTheme` 控制
- 已固化的流程能不能被真实项目 case 复用

### 6.4 这不是终点，而是全阶段优化的分段 gate 口径

当前需要区分两个 `PLATFORM` case：

- `IPD-20260611-PLATFORM-001` 已完成 `ceo-demand -> delivery` 的全链路 proving-ground replay；它证明 IPD 已能跑出全阶段 output、signoff、release version 和 evidence，可作为长期 contract 候选的证据基线。
- `IPD-20260610-PLATFORM-001` 是当前 full-scope 产品主线和后续 Gate A / Gate B / Gate C 的继续验证目标；它应消费 `20260611` 已验证并回写到基线的能力，而不是重新把 `20260611` 当成未完成的 gate 目标。

整个目标应明确写成：**逐步优化并验证全部 IPD 阶段**。推荐分三段推进：

1. Gate A：`ceo-demand -> task-dispatch -> discovery -> intelligence -> package/signoff`
2. Gate B：`designing -> coding -> verify-integration`
3. Gate C：`redteam -> qa -> deployment -> assurance -> delivery`

其中：

- Designing 不只产出技术路线，还要同步产出架构、产品技术选型、MVP 与 full-PRD phased plan、测试基线和 security-by-design 输入。
- Verify-Integration 不是临时想测什么就测什么，而是尽量按 Designing 阶段已经定义好的测试基线执行。
- Redteam 不是最后才想起安全，而是验证 Designing 阶段预置的安全假设和防护方案。

每一轮都走同一套闭环：

1. 先在独立 `process-improvement + WORKFLOW` case 里修流程，当前对应 `IPD-20260612-WORKFLOW-002`
2. 再做 source-side 自测与切片验证
3. 再回到 `IPD-20260610-PLATFORM-001` 做 live replay / 产品主线消费
4. 合格就继续向后放行
5. 不合格就按缺陷来源回退到 `ceo-demand`、`task-dispatch`、`discovery` 或必要的后续阶段
6. 把失败点重新回灌到下一条 workflow sprint case

因此培训和执行时都不要把“当前先验 Gate A”误讲成“IPD 只优化到 D/I 为止”。

## 7. 后续阶段怎样讲给新人

对流程优化 case，培训不需要每一步都背命令细节，但必须让新人理解统一模式：

1. owner 接到当前阶段 work item
2. owner 用 `submit` 提交阶段产物
3. owner 在 `submit` 时对阶段 package hash 自动签名
4. `CEO` 签
5. `CEOChiefOfStaff` 验证前序签名并最终签发版本号
6. 系统自动进入下一阶段

提交示例：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case submit `
  --case-id IPD-20260611-WORKFLOW-001 `
  --stage-key sprint-execution `
  --submitted-by ChiefTechnologyOfficer `
  --summary "提交流程优化的 sprint execution 实施结果" `
  --detail "明确 intake、dispatch、签核链、rollback 和阶段边界的实现收口" `
  --evidence "docs/workflow/agile-improvement/ipd-20260611-workflow-001-sprint-execution.md" `
  --mnemonic "<twelve-or-twenty-four-words>"
```

签核示例：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-20260611-WORKFLOW-001 `
  --stage-key sprint-execution `
  --role CEO `
  --decision approved `
  --signing-key <web3-private-key>

python -m runtime.cognition.chief_of_staff_ipd_case signoff `
  --case-id IPD-20260611-WORKFLOW-001 `
  --stage-key sprint-execution `
  --role CEOChiefOfStaff `
  --decision approved `
  --mnemonic "<twelve-or-twenty-four-words>"
```

## 8. `step` 和 `rollback` 应该怎么讲

### 8.1 `step`

`step` 用来重算 case，让系统按当前状态判断是否需要推进：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case step --case-id IPD-20260611-WORKFLOW-001
```

### 8.2 `rollback`

当前建议把 `rollback` 讲成三类落点：

1. 回到 `ceo-demand`：重新回到 CEO demand / intake 节点
2. 回到 `task-dispatch`：回到总助已分派、当前 flow 首阶段 owner 待重新接单的节点
3. 回到任意正式 stage key：流程优化线例如 `backlog`、`sprint-planning`、`sprint-execution`；项目交付线例如 `discovery`、`intelligence`、`designing`

示例：

```powershell
python -m runtime.cognition.chief_of_staff_ipd_case rollback `
  --case-id IPD-20260611-WORKFLOW-001 `
  --stage-key ceo-demand `
  --reason "需要回到 CEO 提需求重新确认边界"

python -m runtime.cognition.chief_of_staff_ipd_case rollback `
  --case-id IPD-20260611-WORKFLOW-001 `
  --stage-key task-dispatch `
  --reason "需要回到总助分派后的 backlog 接单节点"
```

## 9. 运行态对象会写到哪里

当前默认写到总助 workbench：

- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/case.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/intake-brief.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/events.jsonl`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/work-items/*.json`
- `knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/<case-id>/outputs/*.json`

其中：

- `case.json`：当前 case 主状态
- `intake-brief.json`：当前供总助 / CEO 签核的入口 briefing
- `events.jsonl`：事件流水
- `work-items/*.json`：当前节点工作单
- `outputs/*.json`：owner 提交的节点产物

这些都是运行态对象，不是中央真源文档本身。

## 10. RAndDTrainer 培训时最需要强调什么

1. 入口顺序是 `task-intake -> init -> intake-approve`，不要把 `task-intake` 讲成可跳过命令。
2. `entryCheckpoint` 是入口节点真源，前端、会议流和培训说明都应优先用它解释当前位置。
3. `process-improvement` 和 `project-delivery` 不能混在同一条 case 里。
4. TriCompany 负责公司员工参与、资料组织、书面门禁和核签；TriDev 负责开发执行段 phase engine。
5. `completed` 只表示当前 case 在当前 scope 下完成了一轮公司级交付闭环，不表示“自动化公司已全部完成”。
6. CLI / 代码流程教学应回到 [IPD CLI 与代码工作流程教程（小白版）](ipd-cli-and-code-workflow-beginner-course.md)，避免把概览教程写成源码逐行讲解。

## 11. 真源回链

- `TriCompany/docs/workflow/integrated-product-development-flow.md`
- `TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md`
- `TriCompany/docs/workflow/rd-trainer-role.md`
- `TriCompany/docs/training/ipd-cli-and-code-workflow-beginner-course.md`
- `TriCompany/runtime/cognition/ipd_case_engine.py`
- `TriCompany/runtime/cognition/chief_of_staff_ipd_case.py`
- `TriMetaverse/docs/三元宇宙架构与模块说明.md`
