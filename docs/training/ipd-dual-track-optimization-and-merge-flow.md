# IPD 双线优化与 Merge 流程教程

版本：V0.1（初稿）
日期：2026-07-03
状态：教程草稿，随 IPD 优化深入持续更新

## 文档定位

本文档讲解 TriCompany IPD 的**流程优化线**与**项目交付线**如何协同工作，以及优化成果如何通过 CPO/CTO 审批 merge 回公司级 baseline。

读者：全体赛博公司岗位（CPO、CTO、CEOChiefOfStaff、CMO、COO、CFO），以及对 IPD 运作机制感兴趣的新成员。

前置阅读：
- [integrated-product-development-flow.md](../workflow/integrated-product-development-flow.md) — 公司级 IPD 主流程
- [ipd-usage-guide.md](ipd-usage-guide.md) — IPD CLI 使用指南

---

## 1. 双线总览

```
                      ┌─────────────────────┐
                      │    IPD 双线闭环      │
                      └─────────┬───────────┘
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
  ┌───────▼────────┐                         ┌───────▼────────┐
  │ 流程优化线      │                         │ 项目交付线      │
  │ (process-       │                         │ (project-       │
  │  improvement)   │                         │  delivery)      │
  │                 │                         │                 │
  │ WORKFLOW case   │                         │ CEO demand →    │
  │ Agile sprint    │                         │ 10-stage flow   │
  │                 │                         │                 │
  │ 优化 intake/    │      验证优化成果       │ PLATFORM case   │
  │ dispatch/       │◄──────────────────────►│ proving-ground  │
  │ signoff/stage   │                         │ replay          │
  └───────┬────────┘                         └─────────────────┘
          │
          │ 验证通过
          ▼
  ┌───────────────────┐
  │ 审批 merge        │
  │ CPO + CTO 审批    │
  │ → 主流程文档      │
  │ → runtime 双写    │
  └───────────────────┘
```

- **流程优化线**（`process-improvement`）：用 WORKFLOW case + agile sprint 方式改进 IPD 自身的规则、门禁、签核和阶段语义。**只改流程本身，不直接产出产品。**
- **项目交付线**（`project-delivery`）：正常接收 CEO 需求，走 Discovery → Intelligence → Designing → ... → Delivery 十阶段交付产品。

两条线的衔接：优化线产出 → PLATFORM case proving-ground 验证 → CPO/CTO 审批 → merge 回公司 baseline → 后续所有项目交付 case 自动继承。

---

## 2. 优化 → 审批 → Merge 全链条（实例讲解）

以 `2026-06-11` 到 `2026-07-03` 完成的第一轮优化为例：

### 2.1 第一步：WORKFLOW 提出优化方案

```
WORKFLOW-001 (process-improvement)
  提出 IPD 流程改进方案：
  - Discovery 阶段应生成五件套作为最小交付物
  - Intelligence 阶段应生成四件套
  - PRD 必须基于 CapabilityExtractionMatrix
  - QA 评分体系、Delivery manifest/report 等
```

### 2.2 背景：从验证桩到产品主链的迁移

最初的设计是用 `IPD-20260611-PLATFORM-001` 作为**验证桩（proving-ground stake）**，在上面跑 `IPD-20260611-WORKFLOW-001` 的优化方案。验证桩是一条独立的小型 project-delivery 链路，用于快速验证流程改动是否可行，不影响产品主链。

在 WORKFLOW-001 验证通过后，团队意识到：验证桩能证明"改得通"，但无法证明"在产品主链的全链条上也能跑通"。为了在真实的项目交付主链上做全链条优化验证，决策将验证阵地迁到产品主链 `IPD-20260610-PLATFORM-001`。因为 WORKFLOW-001 的优化是直接在验证桩上跑的，而主链 PLATFORM-001 需要一条能覆盖主链全阶段的优化方案，所以新建了 `IPD-20260612-WORKFLOW-002`，**在吸收 WORKFLOW-001 全部已验证增量的基础上**，补齐了主链特有的需求（approval-backfill rehearsal、Discovery replay 验证链、task-intake 三模式模块路由等）。

换句话说：

```
第一轮（验证桩阶段）：
  IPD-20260611-WORKFLOW-001（优化方案）
        ↓ 验证于
  IPD-20260611-PLATFORM-001（验证桩，小型独立链路）
        ↓ 结论：优化可行，但仅在验证桩上成立

第二轮（产品主链阶段）：
  IPD-20260612-WORKFLOW-002（继承 001 + 补齐主链需求）
        ↓ 验证于
  IPD-20260610-PLATFORM-001（产品主链，全链条项目交付）
        ↓ 结论：优化在主链全阶段可用 → 进入审批 merge
```

这就是为什么会有 WORKFLOW-001 和 WORKFLOW-002 的继承关系——**不是 001 有问题被替换，而是验证阶段递进：验证桩 → 产品主链。**

### 2.3 第二步：PLATFORM 验证桩验证

```
IPD-20260611-PLATFORM-001 (project-delivery, proving-ground stake)
  独立验证桩，全链路 ceo-demand → delivery 跑通
  验证：WORKFLOW-001 提出的规则在实际 case 中是否可行
  产出：真实 stage package、签核记录、release version
  结论：优化可行，但需在主链上进一步验证
```

### 2.4 第三步：WORKFLOW-002 继承并迁移到产品主链

```
IPD-20260612-WORKFLOW-002 (process-improvement)
  吸收 WORKFLOW-001 全部已验证增量
  运行于产品主链 IPD-20260610-PLATFORM-001
  补齐：
  - approval-backfill rehearsal
  - Discovery replay 验证链
  - task-intake 三模式模块路由
```

### 2.5 第四步：backfill-001 审批批次

```
IPD-FIRST-REAL-APPROVAL-BACKFILL-001

CPO 审批（ipd-product-acceptance-contract-cpo-review.md）
  10 项产品验收 contract 审查
  → 7 APPROVE（through-pass）：
    - Discovery 五件套为最小通过条件
    - 无 DiscoveryReferenceFunctionalBrief 不得进 Intelligence
    - Intelligence 四件套为最小通过条件
    - PRD 范围只能来自 CapabilityExtractionMatrix
    - QA = 统一评分 + candidate delivery + readiness
    - Delivery 必须产出 final manifest/report
    - Delivery 不等于生产级上线完成
  → 3 FREEZE（回流下一轮 sprint）：
    - QA 分值阈值
    - 一票否决维度列表
    - candidate→final delivery 门槛

CTO 审批（ipd-runtime-evidence-contract-cto-review.md）
  10 项 runtime evidence contract 审查
  → 8 APPROVE（through-pass，6 项需 runtime 双写）：
    - Scorecard 命名保留
    - templateFields/standardFlow/handoffChecklist 进入稳定 contract
    - 真实 evidence 底线
    - Coding 后不得 docs 假完成
    - packageHash/signatureChain/release 四组对象
    - manual-ceo-signoff 保留
    - simulated wallet 签名原则
    - Deployment/Assurance 分层
  → 2 FREEZE：
    - default seed/mnemonic 细节
    - local-only deployment strategy 细节
```

### 2.6 第五步：Through-Pass Merge

```
CEOChiefOfStaff 执行 merge：

1. 主流程文档合并
   integrated-product-development-flow.md V0.6 → V0.7
   新增 §2.3 第一次真实审批 merge 执行记录
   15 项 APPROVE 标记为长期 contract

2. Runtime 双写（CTO）
   ipd_case_engine.py：
     添加 DST-01 ~ DST-06 contract stability markers
   chief_of_staff_ipd_case_validation.py：
     添加 6 条 test_contract_dst* 验证用例
   6/6 通过

3. FREEZE 回流
   5 项 FREEZE → ipd-long-term-contract-solidification-list.md
   作为下一轮 WORKFLOW sprint backlog seeds

4. Operating record 同步
   W27 OP-202606-W27-001 更新
   CARRY-20260629-006 状态刷新

5. 批次闭合
   backfill-001 batchStatus → completed
```

### 2.7 Merge 前后的关键区别

| | merge 前 | merge 后 |
|---|---|---|
| 五件套/四件套规则 | "PLATFORM-001 跑通了，可以参考" | "这是公司级稳定 contract，新 case 自动继承" |
| 新开 IPD case | 需要手动参考历史 case 的做法 | `initialize_ipd_case` 直接按 contract 生成 stage template |
| 规则修改 | 可以直接改文档 | 必须走新一轮 WORKFLOW → PLATFORM → 审批 |
| PRD 来源约束 | 建议遵循 | `submit_stage_output` 硬校验 |
| 签核 | 可选 | packageHash + signature + release 四组对象全流程记录 |

---

## 3. Merge 后：ceo-demand → Intelligence 业务流

```
CEO 提需求
  │  "做一个统一模型 API 平台"
  ▼
┌─────────────────────────────────────────────┐
│ CEOChiefOfStaff 接单（task-intake）           │
│                                              │
│ 补齐 7 个关键槽位（clarification sheet）：      │
│   competitorReference  竞品/对标对象           │
│   targetUserScenario   首轮目标用户与场景       │
│   deliveryWindow       期望工期/节奏           │
│   budgetGuardrail      预算护栏/成本窗口       │
│   successMetric        首轮成功信号            │
│   mustHaveScope        必须交付的最小范围       │
│   explicitOutOfScope   明确不做项              │
│                                              │
│ 槽位不全 → paused-intake-clarification        │
│ 可行性不成立 → paused-frozen                  │
└───────────────────┬─────────────────────────┘
                    │ 槽位齐全 + 可行性通过
                    ▼
┌─────────────────────────────────────────────┐
│ CEO + CEOChiefOfStaff 签核 intake            │
│ → packageHash + signerAddress + signature    │
│ → release version 发放                       │
└───────────────────┬─────────────────────────┘
                    │ currentStageKey → "discovery"
                    ▼
┌─────────────────────────────────────────────┐
│ 【Discovery】CPO 主责                         │
│                                              │
│ 动作：                                        │
│ 1. 按总助拆解的任务，搜索相关产品与官方手册      │
│ 2. 下载原始材料到                              │
│    TriMetaverse/reference/discovery/<case-id>/│
│ 3. 自动生成五件套：                            │
│    ├─ DiscoveryReferenceFunctionalBrief       │
│    ├─ DiscoveryCompetitorLandscape            │
│    ├─ DiscoveryCommonCapabilityMatrix         │
│    ├─ DiscoveryHighlightOpportunityMemo       │
│    └─ reference-source-catalog.json           │
│                                              │
│ 门禁（merge 后硬约束）：                        │
│ ❌ 五件套不全 → 不允许 submit                  │
│ ❌ 没有 ReferenceFunctionalBrief → 不允许进    │
│    Intelligence（handoffToIntelligence 断言）  │
│                                              │
│ CMO 可在 Discovery 期间冻结 case               │
│ （判断"这不是市场真实需求"）                    │
└───────────────────┬─────────────────────────┘
                    │ CPO 签核
                    ▼
┌─────────────────────────────────────────────┐
│ 【Intelligence】CPO 主责 + CTO 参与           │
│                                              │
│ 动作：                                        │
│ 1. 消费 DiscoveryReferenceFunctionalBrief    │
│ 2. 搜索相关开源代码到                          │
│    TriMetaverse/reference/intelligence/<case-id>/│
│ 3. 建立 CodeGraph（如宿主暂未挂载，先记录锚点） │
│ 4. 自动生成四件套：                            │
│    ├─ IntelligenceCapabilityExtractionMatrix │
│    ├─ IntelligenceOpenSourceLandscape        │
│    ├─ IntelligenceCodegraphAnalysis          │
│    └─ IntelligenceArchitectureOptionMemo     │
│ 5. 基于 ExtractionMatrix 收口正式 PRD         │
│                                              │
│ 门禁（merge 后硬约束）：                        │
│ ❌ PRD 不得直接照搬上游仓库结构                 │
│ ❌ PRD 范围只能来自 ExtractionMatrix 的纳入项   │
│                                              │
│ CTO/COO/CFO 可在各自窗口冻结 case              │
└───────────────────┬─────────────────────────┘
                    │ CPO 签核
                    ▼
┌─────────────────────────────────────────────┐
│ 【Designing】CTO 接班                          │
│ （后续阶段……）                                │
└─────────────────────────────────────────────┘
```

---

## 4. Merge 后：ceo-demand → Intelligence 代码流

### 4.1 代码调用链全景

`initialize_ipd_case()` 首先解析 `case_category`，按两类分叉：

```
initialize_ipd_case(case_id, title, objective, ..., case_category, ...)
  │
  ├─ 解析 case_category
  │    ├─ "project-delivery" → _STAGE_TEMPLATES（十阶段交付流水线）
  │    └─ "process-improvement" → _PROCESS_IMPROVEMENT_STAGE_TEMPLATES（agile sprint）
  │
  ├─ 补齐 clarification sheet（7 槽位）← 两类都走，属于 intake 通用流程
  │
  └─ 按对应模板生成 stage records → 写入 case.json
```

#### A. project-delivery（十阶段交付流水线）

```
1. 入口
   ipd_case_main(["task-intake", "--case-id", "IPD-...", "任务描述"])
     │
     └─→ initialize_ipd_case(case_category="project-delivery")
           │  补齐 clarification sheet（7 槽位）
           │  从 _STAGE_TEMPLATES 生成 10 阶段 record
           │  每个 stage record 含：
           │    - packageHash / releaseCounter / releaseVersion / releaseStatus
           │    - businessOwner / actingOwner / moduleExecutor / gateOwner
           │    - standardFlow / handoffChecklist / templateFields（如适用）
           │  写入 case.json
           │
           └─→ status: "awaiting-intake-approvals"

2. Intake 签核
   record_intake_signoff(case_id, role="CEO", decision="approved")
     │  → _package_hash(_build_intake_signature_payload(case_payload))
     │  → _record_signed_approval()
     │       → _default_wallet_seed(role)  生成 deterministic simulated wallet
     │       → sign_web3_package_hash()    签名
     │  → _issue_release()                 发放 INTAKE release version
     │  → _write_intake_brief()            更新 intake briefing
     │  → _save_case() + _append_event()
     │
     └─→ status → "approved"
         entryCheckpoint → "task-dispatch"
         currentStageKey → "discovery"

3. Discovery 自动化（autopilot 或手动 CLI）
   run_discovery_stage_automation(case_id, submit=True)
     │
     ├─ _build_discovery_sources(case_payload)
     │   → 从 _DISCOVERY_SOURCE_SEEDS 筛选匹配的竞品/官方产品
     │   → 按 referenceTheme 过滤（PLATFORM / WORKFLOW / ...）
     │
     ├─ _write_discovery_documents(case_payload, sources)
     │   → 生成五件套 markdown + reference-source-catalog.json
     │   → 写入 TriMetaverse/reference/discovery/<case-id>/
     │
     ├─ submit_stage_output(case_id, stage_key="discovery", ...)
     │   │
     │   ├─ _require_stage()  找到 discovery stage record
     │   │
     │   ├─ evidence 校验：
     │   │   必须包含 reference-source-catalog.json
     │   │   必须包含 discovery-reference-functional-brief.md
     │   │   必须包含三份 markdown package
     │   │
     │   ├─ _REAL_EXECUTION_STAGE_KEYS 检查：
     │   │   discovery 不在 coding→assurance 六阶段内
     │   │   → 允许 autopilot 自动提交
     │   │
     │   ├─ _stage_standard_flow(template)
     │   │   → 按 standardFlow.requiredActions 逐条检查
     │   │
     │   └─ _package_hash + sign_web3_package_hash
     │       → 写回 stage record 的 packageHash / signerAddress
     │
     └─→ status: "awaiting-stage-approvals"

4. CPO 签核 Discovery → 推进到 Intelligence
   record_stage_signoff(case_id, stage_key="discovery",
                        role="ChiefProductOfficer", decision="approved")
     │  → _issue_release() 发放 DISCOVERY release version
     │  → 激活下一阶段：currentStageKey → "intelligence"
     │
     └─→ status: "active"（intelligence 阶段）

5. Intelligence 自动化
   run_intelligence_stage_automation(case_id, submit=True,
                                     enable_codegraph=True)
     │
     ├─ 前置检查：
     │   必须存在 DiscoveryReferenceFunctionalBrief
     │   （handoffToIntelligence contract）
     │
     ├─ _build_intelligence_sources(case_payload)
     │   → 从 _INTELLIGENCE_SOURCE_SEEDS 筛选匹配的开源代码
     │   → 按 referenceTheme 过滤
     │
     ├─ _collect_codegraph_insights(source)
     │   → 对每个 source 建立本地 CodeGraph
     │   → 返回 contextMarkdown + statusOutput
     │
     ├─ _write_intelligence_documents(case_payload, sources)
     │   → 生成四件套 markdown + reference-source-catalog.json
     │   → 写入 TriMetaverse/reference/intelligence/<case-id>/
     │
     ├─ submit_stage_output(case_id, stage_key="intelligence", ...)
     │   │
     │   ├─ evidence 校验：
     │   │   必须包含 intelligence-capability-extraction-matrix.md
     │   │   必须包含三份 markdown package
     │   │
     │   ├─ PRD 规则（DST-01 contract）：
     │   │   standardFlow.prdRule 要求 PRD 基于 ExtractionMatrix
     │   │   不得照搬上游仓库结构
     │   │
     │   └─ packageHash + signerAddress 记录
     │
     └─→ status: "awaiting-stage-approvals"

6. CPO 签核 Intelligence → 推进到 Designing
   record_stage_signoff(case_id, stage_key="intelligence",
                        role="ChiefProductOfficer", decision="approved")
     │  → _issue_release()
     │  → currentStageKey → "designing"（CTO 接班）
     │
     └─→ Designing 阶段激活……
```

#### B. process-improvement（Agile Sprint 流程优化）

process-improvement case **不走十阶段交付流水线**，而是走 5 阶段 agile sprint：

```
1. 入口
   ipd_case_main(["task-intake", "--case-id", "IPD-...-WORKFLOW-002",
                 "--case-category", "process-improvement", "优化描述"])
     │
     └─→ initialize_ipd_case(case_category="process-improvement")
          │  补齐 clarification sheet（7 槽位）← 同 project-delivery
          │  从 _PROCESS_IMPROVEMENT_STAGE_TEMPLATES 生成 5 阶段 record：
          │    ┌──────────────┬─────────────────────────┬──────────────┐
          │    │ stageKey     │ 阶段                    │ actingOwner  │
          │    ├──────────────┼─────────────────────────┼──────────────┤
          │    │ backlog      │ 流程增量整理             │ CEOChiefOfStaff │
          │    │ sprint-planning │ 迭代计划              │ CEOChiefOfStaff │
          │    │ sprint-execution │ 实施与验证           │ CTO           │
          │    │ sprint-review   │ 阶段评审              │ CPO           │
          │    │ retrospective   │ 复盘固化              │ CEOChiefOfStaff │
          │    └──────────────┴─────────────────────────┴──────────────┘
          │
          └─→ status: "awaiting-intake-approvals"

2. Backlog → Sprint-Planning → Sprint-Execution → Sprint-Review → Retrospective
   产出物写入 TriCompany/docs/workflow/agile-improvement/{caseId}/
   ├─ 01-backlog-memo.md
   ├─ 02-sprint-plan.md
   ├─ 03-sprint-execution-log.md
   ├─ 04-sprint-review-memo.md
   └─ 05-retrospective-memo.md

3. Retrospective 通过后 → 进入审批 merge（与 project-delivery 共享同一审批链路）
   验证通过的流程增量 → CPO + CTO 审批 → merge 回公司 baseline
```

> **关键区别**：project-delivery 的交付物是"产品"（代码、设计、部署），process-improvement 的交付物是"更好的流程规则"。两条线共享 intake（七槽位）、签核（Web3 签名）和审批 merge 机制，但**阶段模板完全不同**。

### 4.2 关键文件映射

| 业务概念 | 代码文件 | 关键位置 |
|----------|----------|----------|
| 十阶段模板 | `runtime/cognition/ipd_case_engine.py` | `_STAGE_TEMPLATES`（第 66 行起） |
| Agile sprint 模板 | 同上 | `_PROCESS_IMPROVEMENT_STAGE_TEMPLATES`（第 713 行起） |
| 七槽位 intake | 同上 | `_INTAKE_CLARIFICATION_SLOT_TEMPLATES`（第 1279 行起） |
| 岗位分配矩阵 | 同上 | `_INTAKE_STAGE_ROLE_ASSIGNMENT_MATRIX`（第 1379 行起） |
| Web3 签核 | `runtime/cognition/web3_signing.py` | `sign_web3_package_hash` / `verify_web3_signature` |
| 自动推进 | `ipd_case_engine.py` | `run_case_autopilot()` |
| 阶段提交 | 同上 | `submit_stage_output()` |
| 阶段签核 | 同上 | `record_stage_signoff()` |
| CLI 入口 | `runtime/cognition/chief_of_staff_ipd_case.py` | `main()` |
| 验证测试 | `runtime/cognition/chief_of_staff_ipd_case_validation.py` | `ChiefOfStaffIpdCaseValidationTest` |
| Discovery seeds | `ipd_case_engine.py` | `_DISCOVERY_SOURCE_SEEDS`（第 924 行起） |
| Intelligence seeds | 同上 | `_INTELLIGENCE_SOURCE_SEEDS`（第 1141 行起） |
| Contract 稳定标记 | 同上 | 文件头顶部 DST-01 ~ DST-06 |
| Agile improvement 产出 | `docs/workflow/agile-improvement/{caseId}/` | 01~05 五份 memo |

### 4.3 Merge 后的 6 项 Runtime Contract（DST markers）
DST Downstream Stability Test，**下游稳定性验证**，用于确保 merge 后的流程规则在后续 case 中不会被破坏。
每条 DST 都有对应的 validation test 做退化防护——改代码后跑  chief_of_staff_ipd_case_validation.py ，哪条断了就报哪条。本质上是"CTO 审批通过后，把口头约定钉进代码注释 + 测试断言"的双写机制。

| 编号 | 合约 | 含义 | 为什么重要 | 退化防护 |
|------|------|------|------------|----------|
| DST-01 | templateFields/standardFlow/handoffChecklist | 阶段模板三件套稳定 | 新增阶段必须照此格式，否则下游自动化断裂 | validation test 断言 |
| DST-02 | 真实 evidence 底线 | `_REAL_EXECUTION_BLOCK_REASON` 常量 | 防止"跑个 autopilot 就当阶段完成" | validation test 检查非空 |
| DST-03 | Coding 后不得 docs 假完成 | `_REAL_EXECUTION_STAGE_KEYS` 六阶段 | 防止"写个 README 就当阶段完成了" | validation test 检查六阶段齐全 |
| DST-04 | packageHash/signatureChain/release | 所有 stage record 含四字段 | 全流程可追溯，每阶段必须有哈希+签名+版本 | validation test 遍历检查 |
| DST-05 | manual-ceo-signoff 保留 | `_AUTOPILOT_OWNER_ACTION_ROLES` 含 CEOChiefOfStaff | autopilot 不能跳过 CEO 签核点 | validation test 检查 |
| DST-06 | simulated wallet 签名原则 | `_default_wallet_seed(role)` 确定性 | 签名协议不走形式，同岗位同 seed 可复验 | validation test 检查同 role 同 seed |

---

## 5. 如何参与下一轮优化

### 如果你发现了流程问题

1. 在 `docs/workflow/operating-records/` 当前周的未决事项中记录
2. CEOChiefOfStaff 在周度平移时判断是否需要开新的 WORKFLOW case
3. 开新的 `process-improvement + WORKFLOW` case → agile sprint → PLATFORM 验证
4. 验证通过后，启动新一轮 backfill 审批
5. 更新本教程

### 当前待优化的 FREEZE 项（下一轮 WORKFLOW backlog seeds）

| 项目 | 冻结原因 | 下一步 |
|------|----------|--------|
| QA 分值阈值 | 语义成立，具体阈值需 sprint 定版 | 后续 sprint 制定 + CPO 审批 |
| 一票否决维度列表 | 维度列表需 sprint 定版 | 同上 |
| candidate→final delivery 门槛 | 门槛条件需 sprint 定版 | 同上 |
| default seed/mnemonic 细节 | 实现细节仍依赖 proving-ground | 待 runtime 成熟后由 CTO 提案 |
| local-only deployment strategy 细节 | 当前仅是 Copilot-host 阶段策略 | 待切换至 TriMC 服务器正式版时重新评估 |

---

## 6. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| V0.1 | 2026-07-03 | 初稿：记录第一轮优化→审批→merge 全链路，覆盖 ceo-demand→Intelligence 业务流与代码流 |
