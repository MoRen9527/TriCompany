# Discovery Guard CTO Focused Self-Test 记录模板

版本：V0.1
日期：2026-06-16
状态：`SP-202A` 首轮实现后的自测记录模板

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/09-cto-focused-self-test-record-template.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首轮 guard 验证完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文是 `ChiefTechnologyOfficer` 在完成 `SP-202A` 后，用来记录 seeded competitor carry-forward guard focused self-test 结果的统一填写面。

本文不替代真实代码实现，也不替代 `CPO` 的 Discovery replay 结果。它只记录：实现范围、自测输入、自测步骤、预期结果、实际结果、差异判断和是否达到 replay-ready。

## 2. 使用顺序

1. `CTO` 完成 carry-forward guard 实现。
2. `CTO` 基于当前 20260610 intake / case 准备 focused self-test。
3. 在本文记录自测输入、步骤和结果。
4. 自测通过后，由 `CEOChiefOfStaff` 依据本文和 [08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md) 判断是否允许 `CPO` 开始 replay。

## 3. 自测批次元信息

- selfTestId: `WF-002-SP202A-SELFTEST-001`
- relatedWorkflowCase: `IPD-20260612-WORKFLOW-002`
- relatedProjectCase: `IPD-20260610-PLATFORM-001`
- operatorRole: `ChiefTechnologyOfficer`
- testStatus: `pending`
- startedAt: ``
- finishedAt: ``
- replayReady: `pending`

## 4. 实现范围记录

- implementationSummary: ``
- touchedFiles:
  - ``
- validationPathSummary: ``
- seededCompetitorRuleSummary: `允许扩展更多竞品，但不得让 seeded competitors 从 catalog / brief / landscape 中静默消失。`

## 5. 自测输入记录

- intakeBriefRef: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json)
- caseRef: [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json)
- seededCompetitors:
  - `LiteLLM`
  - `sub2api`
  - `OpenRouter`
  - `OpenAI API Platform`
- baselineEvidenceRefs:
  - [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/reference-source-catalog.json)
  - [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-reference-functional-brief.md)
  - [../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md](../../../TriMetaverse/reference/discovery/IPD-20260610-PLATFORM-001/discovery-competitor-landscape.md)

## 6. 自测步骤记录表

| 步骤 | 检查动作 | 预期结果 | 实际结果 | 是否通过 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 1 | 读取 intake / case 中的 `competitorReference` | 四个 seeded competitors 完整存在 | pending | pending | - |
| 2 | 执行 guard 前置校验 | 能检测 seeded competitors 是否进入后续引用链 | pending | pending | - |
| 3 | 运行生成或验证路径 | 输出不会静默丢失 seeded competitors | pending | pending | - |
| 4 | 检查 `catalog` 结果 | 四个 seeded competitors 全部存在 | pending | pending | - |
| 5 | 检查 `brief` 结果 | 四个 seeded competitors 全部被引用或纳入问题拆解 | pending | pending | - |
| 6 | 检查 `landscape` 结果 | 四个 seeded competitors 全部有条目 | pending | pending | - |
| 7 | 允许扩展更多竞品的回归检查 | 新增竞品不会导致 seeded competitors 丢失 | pending | pending | - |

## 7. 自测结论

- selfTestSummary: ``
- observedGaps:
  - ``
- passDecision: `pending`
- replayReadyDecision: `pending`
- replayReadyNote: ``

## 8. 最小验证记录

| 验证动作 | 结果 | 执行时间 | 备注 |
| --- | --- | --- | --- |
| guard 相关 runtime / validation 文件诊断 | pending | - | - |
| 自测记录 Markdown 诊断 | pending | - | - |
| seeded competitor coverage spot check | pending | - | - |

## 9. Guardrails

1. 本模板不允许把实现前的预期写成“已通过”。
2. 本模板不允许用手工补文档代替 guard 自测通过。
3. 本模板不允许 `CEOChiefOfStaff` 代填 `CTO` 的自测结论。

## 10. Evidence Surface

- [08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md)
- [08-discovery-replay-validation-package.json](08-discovery-replay-validation-package.json)
- [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/intake-brief.json)
- [../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260610-PLATFORM-001/case.json)
