# IPD 产品与验收 Contract CPO 审批稿

版本：V0.1
日期：2026-06-14
状态：ChiefProductOfficer 审批草案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-product-acceptance-contract-cpo-review.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待 CPO 批准后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-14

## 1. 文档定位

本文只处理 `ChiefProductOfficer` 负责的产品 / 验收 contract，不覆盖 runtime schema、evidence policy 或签核技术细节。

它的目标不是重新解释 IPD，而是把已经在 `IPD-20260611-PLATFORM-001` proving-ground replay 中验证过的产品侧语义，整理成一份可审批、可勾选、可回灌到主流程真源的收口稿。

本文的上游总清单是 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)。

## 2. 当前审批边界

当前审批只覆盖以下四类内容：

1. `Discovery` 的最小产品输入 contract。
2. `Intelligence` 的最小产品收口 contract。
3. `QA` 的产品验收语义与放行门槛框架。
4. `Delivery` 的产品完成定义与对象切换条件。

当前明确不在本稿内审批的内容：

1. `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 的 runtime schema 细节。
2. `autopilot`、`manual-ceo-signoff`、签名 seed、proof object 等技术实现。
3. `Deployment / Assurance` 的技术证据策略。

## 3. 已核查依据

当前审批稿直接建立在以下材料上：

1. 主流程真源：[integrated-product-development-flow.md](integrated-product-development-flow.md)
2. 总清单：[ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
3. proving-ground case 终态：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/case.json)
4. Discovery output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/01-discovery.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/01-discovery.json)
5. Intelligence output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/02-intelligence.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/02-intelligence.json)
6. QA output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/07-qa.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/07-qa.json)
7. Delivery output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/10-delivery.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/10-delivery.json)

## 4. CPO 审批结论模板

当前审批结论只允许三类：

1. `APPROVE`：直接进入长期产品 / 验收 contract。
2. `FREEZE`：语义成立，但阈值、边界或分层还不足以进入长期 contract。
3. `REVISE`：当前定义会导致 live case 误判，需要先重写再审。

## 5. Discovery 产品 Contract 审批项

### 5.1 建议结论

建议：`APPROVE`

### 5.2 拟固化内容

1. `Discovery` 至少交付五件套：`reference-source-catalog.json`、`DiscoveryReferenceFunctionalBrief`、`DiscoveryCompetitorLandscape`、`DiscoveryCommonCapabilityMatrix`、`DiscoveryHighlightOpportunityMemo`。
2. 如果没有 `DiscoveryReferenceFunctionalBrief`，不允许直接进入 `Intelligence`。
3. `Discovery` 的目标不是“搜到一些链接”，而是形成可消费的产品输入 contract。
4. `Discovery` 输出必须显式区分：共性能力、差异化机会、边界、不做项、待验证问题。

### 5.3 CPO 待确认项

1. 五件套里哪些属于硬性必交，哪些允许在低风险 case 中降级。
2. `DiscoveryCommonCapabilityMatrix` 是否必须具备“纳入 / 后置 / 排除”三栏。
3. `DiscoveryHighlightOpportunityMemo` 是否必须包含“为什么不是当前轮次必做”的反向约束字段。

## 6. Intelligence 产品 Contract 审批项

### 6.1 建议结论

建议：`APPROVE`

### 6.2 拟固化内容

1. `Intelligence` 必须消费 `DiscoveryReferenceFunctionalBrief`，不允许跳过 Discovery 直接写 PRD。
2. `Intelligence` 至少交付四件套：`IntelligenceCapabilityExtractionMatrix`、`IntelligenceOpenSourceLandscape`、`IntelligenceCodegraphAnalysis`、`IntelligenceArchitectureOptionMemo`。
3. `IntelligenceCapabilityExtractionMatrix` 必须承担产品范围收口职责，至少区分：纳入、后置、排除。
4. `Intelligence` 阶段必须把测试、安全、并发 / 稳定性风险和运行前置条件前传给 `Designing`。

### 6.3 CPO 待确认项

1. `PRD` 与 `IntelligenceCapabilityExtractionMatrix` 的绑定强度。
当前建议是：PRD 的核心功能范围只能来自该矩阵的“纳入项”。
2. `IntelligenceArchitectureOptionMemo` 中哪些内容必须进入 PRD，哪些只保留为技术协同背景。
3. COO / CFO 的运营 / 预算输入，在产品侧是否要求作为 Intelligence 放行前置项，还是允许先占位后补。

## 7. QA 产品验收 Contract 审批项

### 7.1 建议结论

建议：`APPROVE with threshold freeze`

### 7.2 拟固化内容

1. `QA` 的语义固定为：统一质量评分、candidate delivery manifest、candidate delivery report、release readiness 判断。
2. `QA` 不是“测试跑过一次”的别名，而是产品验收前的统一收口层。
3. `QA scorecard` 至少覆盖：设计缺陷、代码质量、架构合理性、测试覆盖率、回归情况、残余 bug 与修复成本、安全评估、并发性、稳定性、健壮性。
4. `candidate delivery manifest` 与 `candidate delivery report` 必须作为独立对象存在，不能只写在 narrative summary 里。

### 7.3 当前继续冻结的项目

1. 各分数维度的具体阈值。
2. 哪些维度属于一票否决项。
3. `ready / hold / reject` 与分数区间的精确映射。

### 7.4 CPO 待确认项

1. 首轮长期规则是否使用三段式判定：`ready / conditional / reject`。
2. `candidate delivery report` 是否必须包含“未修复问题成本”和“后续发布风险”的标准字段。
3. 是否允许不同类型 case 采用不同 scorecard 权重，但继续共用同一字段框架。

## 8. Delivery 产品完成定义审批项

### 8.1 建议结论

建议：`APPROVE with boundary clarification`

### 8.2 拟固化内容

1. `Delivery` 必须至少交付 `final delivery manifest` 与 `final delivery report`。
2. `Delivery` 表示产品侧完成当前轮次放行，不等于自动宣称“生产级上线完成”。
3. `Delivery` 必须显式区分“对内 proving-ground 完成”“对外可交付完成”“正式上线完成”这三层语义。
4. 只有在 `QA` 已形成 candidate delivery 对象、且 `Deployment / Assurance` 已有对应结论后，才允许进入 `Delivery`。

### 8.3 CPO 待确认项

1. `candidate delivery` 升级到 `final delivery` 的正式门槛。
2. `final delivery report` 是否必须包含“后续 live case 是否需要重复验证”的结论字段。
3. 产品侧是否要求在 Delivery 中显式写出“本轮不做项是否仍成立”。

## 9. CPO 审批勾选表

| 审批项 | 当前建议 | 建议动作 |
| --- | --- | --- |
| Discovery 五件套为最小通过条件 | APPROVE | 固化到主流程真源 |
| 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | APPROVE | 固化到放行规则 |
| Intelligence 四件套为最小通过条件 | APPROVE | 固化到主流程真源 |
| PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | APPROVE | 写入产品 contract |
| QA = 统一评分 + candidate delivery 对象 + readiness 判断 | APPROVE | 固化到验收 contract |
| QA 具体分值阈值 | FREEZE | 后续单独定版 |
| 一票否决维度列表 | FREEZE | 后续单独定版 |
| Delivery 必须产出 final manifest / report | APPROVE | 固化到交付 contract |
| Delivery 不等于生产级上线完成 | APPROVE | 固化到边界说明 |
| candidate delivery 升 final delivery 的门槛 | FREEZE | 后续单独定版 |

## 10. 风险

1. 如果 CPO 只批准字段名，不批准通过条件，live case 仍会在放行口径上反复摇摆。
2. 如果 `QA` 阶段只批准“有 scorecard”而不批准 readiness 语义，后续仍可能退化回“测试跑过即可交付”。
3. 如果 `Delivery` 不显式区分 proving-ground 完成与生产完成，经营记录和对外交付口径会再次混写。

## 11. 建议下一步

1. 由 `ChiefProductOfficer` 在本文上逐项标记 `APPROVE / FREEZE / REVISE`。
2. 标记完成后，由 `CEOChiefOfStaff` 把结果回灌到 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)。
3. 待 `CTO` 审批稿完成后，再合并回 [integrated-product-development-flow.md](integrated-product-development-flow.md) 与后续 runtime contract 更新。

## 12. 审批结果回填模板

### 12.0 填写顺序提示

第一次真实审批回填时，`ChiefProductOfficer` 固定按以下顺序填写：

1. 先核对 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 中属于 `CPO` 的首批 through-pass 项。
2. 再确认 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `batchStartedAt` 与 `currentOperator` 已写，避免在未启动批次实例时直接写审批结论。
3. 再填写 `12.1 审批元信息`，至少补齐 `reviewStatus`、`reviewedAt`、`decisionSummary`。
4. 然后填写 `12.2 审批结果表`，优先完成首批 through-pass 项的真实 `最终决定`。
5. 最后填写 `12.4 签发区` 的 `reviewerDecision`、`signoffRecordedAt` 与 `mergeReady`。
6. 本稿填写完成后，立即同步回 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `4.1` 与 `4.2`，不要只停留在本稿。

### 12.1 审批元信息

- reviewerRole: `ChiefProductOfficer`
- reviewStatus: `completed`
- reviewedAt: `2026-07-03T17:39:00+08:00`
- decisionSummary: `首批 7 项 APPROVE（through-pass）：Discovery 五件套、Intelligence 四件套、PRD 来源约束、QA 评分语义、Delivery final manifest/report、Delivery 不等于生产上线、Discovery→Intelligence 前置依赖。3 项 FREEZE：QA 分值阈值、一票否决维度列表、candidate→final delivery 门槛——语义成立但阈值/边界需后续 sprint 定版再升级。`
- sourceReplayCase: `IPD-20260611-PLATFORM-001`
- callbackChecklist: [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
- mergeTarget: [integrated-product-development-flow.md](integrated-product-development-flow.md)
- executionInstance: [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- preStartCheck: `确认 executionInstance 中 batchStartedAt / currentOperator 已填写`
- mergeHooks: `CPO-Discovery-Contract | CPO-Intelligence-Contract | CPO-QA-Delivery-Contract`

### 12.2 审批结果表

| 审批项 | merge hook | 当前建议 | 最终决定 | 备注 |
| --- | --- | --- | --- | --- |
| Discovery 五件套为最小通过条件 | `CPO-Discovery-Contract` | APPROVE | APPROVE | - |
| 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | `CPO-Discovery-Contract` | APPROVE | APPROVE | - |
| Intelligence 四件套为最小通过条件 | `CPO-Intelligence-Contract` | APPROVE | APPROVE | - |
| PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | `CPO-Intelligence-Contract` | APPROVE | APPROVE | - |
| QA = 统一评分 + candidate delivery 对象 + readiness 判断 | `CPO-QA-Delivery-Contract` | APPROVE | APPROVE | - |
| QA 具体分值阈值 | `CPO-QA-Delivery-Contract` | FREEZE | FREEZE | 阈值需后续 sprint 定版 |
| 一票否决维度列表 | `CPO-QA-Delivery-Contract` | FREEZE | FREEZE | 维度列表需后续 sprint 定版 |
| Delivery 必须产出 final manifest / report | `CPO-QA-Delivery-Contract` | APPROVE | APPROVE | - |
| Delivery 不等于生产级上线完成 | `CPO-QA-Delivery-Contract` | APPROVE | APPROVE | - |
| candidate delivery 升 final delivery 的门槛 | `CPO-QA-Delivery-Contract` | FREEZE | FREEZE | 门槛条件需后续 sprint 定版 |

### 12.3 回灌动作

| 动作 | owner | 目标文件 | 状态 |
| --- | --- | --- | --- |
| 把 `APPROVE` 项回写到主 IPD 流程真源 | CEOChiefOfStaff | [integrated-product-development-flow.md](integrated-product-development-flow.md) | pending |
| 把 `FREEZE / REVISE` 项回写到长期总清单 | CEOChiefOfStaff | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) | pending |
| 需要转交 CTO 协同的边界项汇总 | CEOChiefOfStaff | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | pending |

### 12.4 签发区

- reviewerDecision: `APPROVE`
- reviewerNote: `7 项 through-pass 进入主流程 merge，3 项 FREEZE 回流长期清单待后续 sprint 定版`
- escalationRequired: `no`
- followUpSprintNeeded: `yes`
- signoffRecordedAt: `2026-07-03T17:39:00+08:00`
- mergeReady: `yes`
