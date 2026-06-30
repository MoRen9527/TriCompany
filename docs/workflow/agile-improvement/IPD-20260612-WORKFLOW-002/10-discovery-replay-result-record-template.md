# IPD-20260610 Discovery Replay 结果记录模板

版本：V0.1
日期：2026-06-16
状态：非破坏性 replay 结果统一记录面

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/10-discovery-replay-result-record-template.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首轮 replay 完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文用于记录 `IPD-20260610-PLATFORM-001` 在 seeded competitor carry-forward guard 上线后的首轮非破坏性 Discovery replay 结果。

本文不替代 Discovery 五件套本身，也不替代 `CTO` 的 focused self-test 记录。它只提供一份由 `CEOChiefOfStaff` 汇总、`CPO` 参与确认的 replay 结果面。

## 2. 使用顺序

1. 先确认 [09-cto-focused-self-test-record-template.md](09-cto-focused-self-test-record-template.md) 已完成并达到 replay-ready。
2. `CPO` 基于同一 intake 执行 Discovery replay。
3. `CEOChiefOfStaff` 在本文记录 replay 输出、seeded competitor 覆盖情况、差异对比和最终处置。
4. 如失败，则把结论回流 `WORKFLOW-002`；如通过，则保留结果作为首轮 guard 验证证据。

## 3. Replay 批次元信息

- replayRecordId: `WF-002-DISCOVERY-REPLAY-001`
- relatedWorkflowCase: `IPD-20260612-WORKFLOW-002`
- relatedProjectCase: `IPD-20260610-PLATFORM-001`
- coordinatorRole: `CEOChiefOfStaff`
- replayOperatorRole: `ChiefProductOfficer`
- replayStatus: `pending`
- startedAt: ``
- finishedAt: ``
- finalDisposition: `pending`

## 4. 输入与基线记录

- intakeBriefRef: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json)
- caseRef: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json)
- ctoSelfTestRecordRef: [09-cto-focused-self-test-record-template.md](09-cto-focused-self-test-record-template.md)
- baselineCatalogRef: [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json)
- baselineBriefRef: [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md)
- baselineLandscapeRef: [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md)

## 5. Replay 输出记录

- replayCatalogRef: ``
- replayBriefRef: ``
- replayLandscapeRef: ``
- replayMatrixRef: ``
- replayMemoRef: ``
- additionalCompetitorsObserved:
  - ``

## 6. Seeded Competitor 覆盖结果表

| seeded competitor | baseline catalog | replay catalog | replay brief | replay landscape | 是否通过 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `LiteLLM` | pending | pending | pending | pending | pending | - |
| `sub2api` | pending | pending | pending | pending | pending | - |
| `OpenRouter` | pending | pending | pending | pending | pending | - |
| `OpenAI API Platform` | pending | pending | pending | pending | pending | - |

## 7. 差异与结论

- comparisonSummary: ``
- missingCompetitors:
  - ``
- replayNotes:
  - ``
- cpoDisposition: `pending`
- chiefOfStaffDisposition: `pending`
- finalDispositionReason: ``

## 8. 最小验证记录

| 验证动作 | 结果 | 执行时间 | 备注 |
| --- | --- | --- | --- |
| replay Discovery 五件套诊断 | pending | - | - |
| seeded competitor 对照检查 | pending | - | - |
| replay 结果记录 Markdown 诊断 | pending | - | - |
| 若涉及技术改动的 Python 诊断 | pending | - | 仅在 guard 实现有代码改动时填写 |

## 9. 后续动作

- passFollowUp: `保留 replay 输出并将结论写回 WORKFLOW-002 执行资产。`
- revisionRequiredFollowUp: `冻结在 Discovery，并把缺口回流 CTO 的 guard 实现与 WORKFLOW-002 backlog。`
- blockedFollowUp: `先恢复 baseline/archive 路径，再重新安排 replay。`

## 10. Guardrails

1. 本模板不允许把 baseline 被删除后的重跑写成有效验证。
2. 本模板不允许把“新增更多竞品”写成 seeded competitors 丢失的豁免理由。
3. 本模板不允许 `CEOChiefOfStaff` 代替 `CPO` 填产品侧 replay 结论。

## 11. Evidence Surface

- [08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md)
- [08-discovery-replay-validation-package.json](08-discovery-replay-validation-package.json)
- [09-cto-focused-self-test-record-template.md](09-cto-focused-self-test-record-template.md)
