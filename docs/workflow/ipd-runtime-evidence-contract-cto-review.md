# IPD Runtime 与 Evidence Contract CTO 审批稿

版本：V0.1
日期：2026-06-14
状态：ChiefTechnologyOfficer 审批草案

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-runtime-evidence-contract-cto-review.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待 CTO 批准后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-14

## 1. 文档定位

本文只处理 `ChiefTechnologyOfficer` 负责的 runtime contract、evidence policy、签核策略和后段阶段门禁，不覆盖产品范围、PRD 放行或产品完成定义。

它的目标是把 `IPD-20260611-PLATFORM-001` 的 proving-ground replay、`ipd_case_engine.py` 当前已实现 contract，以及 `WORKFLOW-002` 的流程优化线，整理成一份技术侧可审批、可冻结、可回灌的收口稿。

本文的上游总清单是 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)。

## 2. 当前审批边界

当前审批只覆盖以下五类内容：

1. `DesignReviewScorecard`、`QaScorecard`、`AssuranceScorecard` 的 schema 固化策略。
2. `Designing / QA / Assurance` 的 `templateFields`、`standardFlow`、`handoffChecklist` 与 draft exposure contract。
3. `Verify-Integration / Redteam / QA / Deployment / Assurance` 的最小 evidence policy。
4. `packageHash + signatureChain + release issuance` 的 runtime 对象语义。
5. `manual-ceo-signoff`、`auto_approve_roles`、simulated wallet 与 proving-ground / 常态 runtime 的边界。

当前明确不在本稿内审批的内容：

1. `Discovery / Intelligence / QA / Delivery` 的产品完成定义与产品阈值。
2. `candidate delivery` 与 `final delivery` 的产品放行门槛。
3. 对外发布、正式宿主、生产级部署策略。

## 3. 已核查依据

当前审批稿直接建立在以下材料上：

1. 主流程真源：[integrated-product-development-flow.md](integrated-product-development-flow.md)
2. 总清单：[ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
3. runtime 真源：[runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
4. 聚焦回归：[runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
5. Designing output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/03-designing.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/03-designing.json)
6. Verify-Integration output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/05-verify-integration.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/05-verify-integration.json)
7. Redteam output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/06-redteam.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/06-redteam.json)
8. QA output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/07-qa.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/07-qa.json)
9. Deployment output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/08-deployment.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/08-deployment.json)
10. Assurance output：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/09-assurance.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/outputs/09-assurance.json)

## 4. CTO 审批结论模板

当前审批结论只允许三类：

1. `APPROVE`：进入长期 runtime / evidence contract。
2. `FREEZE`：语义成立，但仍应停留在 proving-ground 或待 schema 拆分层。
3. `REVISE`：当前 contract 会误导执行或形成不稳定 API，需要先重写再审。

## 5. Stage Template 与 Schema 审批项

### 5.1 建议结论

建议：`APPROVE with schema-family follow-up`

### 5.2 拟固化内容

1. `DesignReviewScorecard`、`QaScorecard`、`AssuranceScorecard` 继续作为正式 scorecard 名称保留。
2. `Designing / QA / Assurance` 在 runtime draft template 中暴露 `templateFields`、`scorecardSchema`、`standardFlow`、`submissionTemplate`、`handoffChecklist`。
3. `stageKey / phaseKey / businessOwner / actingOwner / moduleExecutor / gateOwner` 继续作为统一阶段 contract 核心字段保留。
4. `_draft_template(...)` 暴露出的 contract 字段应保持稳定，供后续文档、审批和 host runtime 消费。

### 5.3 CTO 待确认项

1. 这些 scorecard schema 是否仍以内嵌 dict 形式留在 `ipd_case_engine.py`，还是拆到独立 schema family。
2. `submissionTemplate` 与 `handoffChecklist` 是否需要单独 objectType / schema version。
3. `standardFlow` 是否应作为可机读 contract 对外稳定暴露，而不只是当前内部模板语义。

## 6. Evidence Policy 审批项

### 6.1 建议结论

建议：`APPROVE`

### 6.2 拟固化内容

1. 任一阶段至少要有一个非纯生成物 evidence path。
2. `Coding` 及后续阶段必须具备真实工程或真实验证 evidence，不允许只用 docs / workbench / autopilot 生成物假完成。
3. `Verify-Integration` 至少绑定测试或集成验证 evidence。
4. `Redteam` 至少绑定安全审查或边界复核 evidence。
5. `QA` 至少绑定 scorecard 与 candidate delivery 对象。
6. `Deployment` 至少绑定 deployment evidence 与 rollout plan。
7. `Assurance` 至少绑定 runtime observation、recovery validation 与 assurance evidence。

### 6.3 CTO 待确认项

1. 各阶段 evidence 的最小对象类型是否要显式机读化，例如 `test-report`、`security-report`、`deployment-record`、`assurance-record`。
2. “真实工程 evidence”的判定规则是否继续沿用当前 runtime 内部检查，还是提炼成单独 validator。
3. `objectPath` 是否必须始终指向该阶段的主 evidence object。

## 7. 签核与 Release Contract 审批项

### 7.1 建议结论

建议：`APPROVE`

### 7.2 拟固化内容

1. intake 与 stage output 继续统一使用 `packageHash`、`signaturePolicy`、`signatureChain`、`release` 四组对象。
2. `approvalOrder`、`finalIssuerRole`、`verificationStatus` 继续作为签核链稳定字段。
3. 每个阶段完成后必须落 `release.status / version / issuedAt / issuedByRole`，不能只凭审批状态表达放行。
4. `CEOChiefOfStaff` 继续作为最终签发角色保留当前版本发行责任。

### 7.3 CTO 待确认项

1. `release issuance` 是否拆成独立 schema family，而不是继续内嵌在 `stage-output` 中。
2. `signatureChain` 是否需要额外字段标识“人工签”与“自动签”的来源模式。
3. `packageHash` 的生成与验证逻辑是否要进一步抽到独立 runtime module contract。

## 8. manual-ceo-signoff 与 autopilot 审批项

### 8.1 建议结论

建议：`APPROVE with proving-ground boundary`

### 8.2 拟固化内容

1. `autopilot` 自动签不等于跳过签名，而是继续走 deterministic simulated wallet 的签名协议。
2. `manual-ceo-signoff` 与 `auto_approve_roles` 继续保留为可控制自动推进的 runtime 开关。
3. 常态 runtime 可以保留 simulated wallet 能力，但不得把当前 proving-ground seed 细节写成长期对外 contract。

### 8.3 当前继续冻结的项目

1. default seed / mnemonic 的具体规则。
2. proving-ground 当前的 signer address / credential hint 细节。
3. 任何会把当前模拟凭据误读为正式授权体系的外显描述。

## 9. Deployment 与 Assurance 技术分层审批项

### 9.1 建议结论

建议：`APPROVE`

### 9.2 拟固化内容

1. `Deployment` 与 `Assurance` 继续作为两个独立阶段存在，不合并。
2. `Deployment` 负责部署策略、上线窗口、rollout plan 与 deployment evidence。
3. `Assurance` 负责运行观察、恢复验证、告警 / 性能 / 成本复核与残余风险追踪。
4. `local-only` 的具体部署策略只证明当前 proving-ground 可回放，不直接升级为长期默认部署方案。

### 9.3 CTO 待确认项

1. `Deployment` 与 `Assurance` 是否都需要独立 scorecard，还是只保留 Assurance scorecard。
2. `Assurance` 的 observation window 与 recovery validation 是否需要正式 machine-readable schema。
3. 是否需要为后续 live case 引入不同 deployment mode 枚举，而不是继续使用 narrative strategy text。

## 10. CTO 审批勾选表

| 审批项 | 当前建议 | 建议动作 |
| --- | --- | --- |
| `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 命名保留 | APPROVE | 固化命名，后续再决定拆 schema |
| `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | APPROVE | 保留字段并稳定暴露 |
| 真实 evidence 底线 | APPROVE | 固化到 validator 规则 |
| `Coding` 后不得 docs 假完成 | APPROVE | 继续作为硬门禁 |
| `packageHash / signatureChain / release` 四组对象 | APPROVE | 固化为稳定 runtime 字段 |
| `manual-ceo-signoff` 保留 | APPROVE | 作为常态 runtime 开关 |
| simulated wallet 的签名原则 | APPROVE | 原则保留，seed 细节冻结 |
| default seed / mnemonic 细节 | FREEZE | 保留在 proving-ground 层 |
| `Deployment / Assurance` 分层 | APPROVE | 固化双阶段分工 |
| local-only deployment strategy 细节 | FREEZE | 不直接升为长期默认策略 |

## 11. 风险

1. 如果 CTO 只批准字段名，不批准 evidence policy，后续仍会出现“对象看起来齐全但证据不真实”的假完成回潮。
2. 如果过早冻结当前 proving-ground 的 seed、路径和 local-only 部署方案，会把样例实现误当成正式 runtime API。
3. 如果不把 `release issuance` 与 `stage output` 的语义稳定下来，后续 host runtime 与 source runtime 仍可能分叉。

## 12. 建议下一步

1. 由 `ChiefTechnologyOfficer` 在本文上逐项标记 `APPROVE / FREEZE / REVISE`。
2. 标记完成后，由 `CEOChiefOfStaff` 把结果回灌到 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)。
3. 等 `CPO` 与 `CTO` 两侧审批稿都有结论后，再合并回 [integrated-product-development-flow.md](integrated-product-development-flow.md) 与 runtime source。

## 13. 审批结果回填模板

### 13.0 填写顺序提示

第一次真实审批回填时，`ChiefTechnologyOfficer` 固定按以下顺序填写：

1. 先核对 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 中属于 `CTO` 的首批 through-pass 项。
2. 再确认 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `batchStartedAt` 与 `currentOperator` 已写，避免在未启动批次实例时直接写审批结论。
3. 再填写 `13.1 审批元信息`，至少补齐 `reviewStatus`、`reviewedAt`、`decisionSummary`。
4. 然后填写 `13.2 审批结果表`，优先完成首批 through-pass 项的真实 `最终决定`。
5. 最后填写 `13.4 签发区` 的 `reviewerDecision`、`signoffRecordedAt` 与 `mergeReady`。
6. 本稿填写完成后，立即同步回 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `5.1`、`5.2` 与 `6.2`，不要只停留在本稿。

### 13.1 审批元信息

- reviewerRole: `ChiefTechnologyOfficer`
- reviewStatus: `pending`
- reviewedAt: ``
- decisionSummary: ``
- sourceReplayCase: `IPD-20260611-PLATFORM-001`
- callbackChecklist: [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
- mergeTargetFlow: [integrated-product-development-flow.md](integrated-product-development-flow.md)
- mergeTargetRuntime: [runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
- mergeTargetValidation: [runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
- executionInstance: [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- preStartCheck: `确认 executionInstance 中 batchStartedAt / currentOperator 已填写`
- mergeHooks: `CTO-Stage-Template-Contract | CTO-Evidence-Policy-Contract | CTO-Signing-Release-Contract`

### 13.2 审批结果表

| 审批项 | merge hook | 当前建议 | 最终决定 | 备注 |
| --- | --- | --- | --- | --- |
| `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 命名保留 | `CTO-Stage-Template-Contract` | APPROVE | pending | - |
| `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | `CTO-Stage-Template-Contract` | APPROVE | pending | - |
| 真实 evidence 底线 | `CTO-Evidence-Policy-Contract` | APPROVE | pending | - |
| `Coding` 后不得 docs 假完成 | `CTO-Evidence-Policy-Contract` | APPROVE | pending | - |
| `packageHash / signatureChain / release` 四组对象 | `CTO-Signing-Release-Contract` | APPROVE | pending | - |
| `manual-ceo-signoff` 保留 | `CTO-Signing-Release-Contract` | APPROVE | pending | - |
| simulated wallet 的签名原则 | `CTO-Signing-Release-Contract` | APPROVE | pending | - |
| default seed / mnemonic 细节 | `CTO-Signing-Release-Contract` | FREEZE | pending | - |
| `Deployment / Assurance` 分层 | `CTO-Evidence-Policy-Contract` | APPROVE | pending | - |
| local-only deployment strategy 细节 | `CTO-Evidence-Policy-Contract` | FREEZE | pending | - |

### 13.3 回灌动作

| 动作 | owner | 目标文件 | 状态 |
| --- | --- | --- | --- |
| 把 `APPROVE` 项回写到主 IPD 流程真源 | CEOChiefOfStaff | [integrated-product-development-flow.md](integrated-product-development-flow.md) | pending |
| 把 runtime contract 结论回写到 source runtime | CEOChiefOfStaff + CTO | [runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) | pending |
| 把回归要求回写到验证文件 | CEOChiefOfStaff + CTO | [runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | pending |
| 把 `FREEZE / REVISE` 项回写到长期总清单 | CEOChiefOfStaff | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) | pending |

### 13.4 签发区

- reviewerDecision: `pending`
- reviewerNote: ``
- escalationRequired: `no`
- followUpSprintNeeded: `yes/no`
- signoffRecordedAt: ``
- mergeReady: `yes/no`
