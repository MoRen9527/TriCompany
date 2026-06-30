# IPD 第一次真实审批回填记录模板

版本：V0.1
日期：2026-06-15
状态：第一次真实审批回填填写模板

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-backfill-record-template.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首次真实审批回填完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文是第一次真实审批回填的填写模板。

它不替代 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 或 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 里的正式审批结果，而是给本轮执行提供一份统一记录面，便于 `CEOChiefOfStaff` 在同轮汇总 `CPO / CTO` 的真实结论、回写动作、冻结回流和验证结果。

## 2. 使用顺序

1. 先按 [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md) 执行真实审批。
2. 再按 [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md) 判断每个项目的 landing zone。
3. 若只做首批 through-pass，优先按 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 的顺序执行。
4. 然后在本模板中记录本轮真实结果。
5. 最后把需要长期保留的状态同步回审批稿、长期清单、`WORKFLOW-002` backlog seeds 和 operating record。

## 3. 回填批次元信息

- batchId: `IPD-FIRST-REAL-APPROVAL-BACKFILL-001`
- sourceReplayCase: `IPD-20260611-PLATFORM-001`
- sourceWorkflowCase: `IPD-20260612-WORKFLOW-002`
- coordinatorRole: `CEOChiefOfStaff`
- batchStatus: `pending`
- batchStartedAt: ``
- batchClosedAt: ``
- operatingRecordTarget: [../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md](../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md)
- machineObjectTarget: [../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.json](../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.json)

## 4. `CPO` 真实回填记录模板

### 4.1 审批元信息

- reviewerRole: `ChiefProductOfficer`
- reviewStatus: `pending`
- reviewedAt: ``
- decisionSummary: ``
- reviewerDecision: `pending`
- reviewerNote: ``
- mergeReady: `yes/no`
- signoffRecordedAt: ``

### 4.2 审批项记录表

| 审批项 | merge hook | 真实结论 | 是否回写主流程 | 是否冻结回流 | 目标落点 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| Discovery 五件套为最小通过条件 | `CPO-Discovery-Contract` | pending | pending | pending | `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | - |
| 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | `CPO-Discovery-Contract` | pending | pending | pending | `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | - |
| Intelligence 四件套为最小通过条件 | `CPO-Intelligence-Contract` | pending | pending | pending | `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | - |
| PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | `CPO-Intelligence-Contract` | pending | pending | pending | `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | - |
| QA = 统一评分 + candidate delivery 对象 + readiness 判断 | `CPO-QA-Delivery-Contract` | pending | pending | pending | `4. IPD 主动交付线` 与 `6. 关键门禁` | - |
| QA 具体分值阈值 | `CPO-QA-Delivery-Contract` | pending | pending | pending | `长期清单 / 下一轮 backlog` | - |
| 一票否决维度列表 | `CPO-QA-Delivery-Contract` | pending | pending | pending | `长期清单 / 下一轮 backlog` | - |
| Delivery 必须产出 final manifest / report | `CPO-QA-Delivery-Contract` | pending | pending | pending | `4. IPD 主动交付线` 的 `Delivery` 阶段说明 | - |
| Delivery 不等于生产级上线完成 | `CPO-QA-Delivery-Contract` | pending | pending | pending | `Delivery` 边界说明与 `7. 当前阶段边界` | - |
| candidate delivery 升 final delivery 的门槛 | `CPO-QA-Delivery-Contract` | pending | pending | pending | `长期清单 / 下一轮 backlog` | - |

## 5. `CTO` 真实回填记录模板

### 5.1 审批元信息

- reviewerRole: `ChiefTechnologyOfficer`
- reviewStatus: `pending`
- reviewedAt: ``
- decisionSummary: ``
- reviewerDecision: `pending`
- reviewerNote: ``
- mergeReady: `yes/no`
- signoffRecordedAt: ``

### 5.2 审批项记录表

| 审批项 | merge hook | 真实结论 | 是否回写主流程 | 是否双写 runtime | 是否冻结回流 | 目标落点 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 命名保留 | `CTO-Stage-Template-Contract` | pending | pending | pending | pending | `4. IPD 主动交付线` + runtime / validation source | - |
| `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | `CTO-Stage-Template-Contract` | pending | pending | pending | pending | `4. IPD 主动交付线` + runtime / validation source | - |
| 真实 evidence 底线 | `CTO-Evidence-Policy-Contract` | pending | pending | pending | pending | `6. 关键门禁` + runtime / validation source | - |
| `Coding` 后不得 docs 假完成 | `CTO-Evidence-Policy-Contract` | pending | pending | pending | pending | `6. 关键门禁` 与 `7. 当前阶段边界` + runtime / validation source | - |
| `packageHash / signatureChain / release` 四组对象 | `CTO-Signing-Release-Contract` | pending | pending | pending | pending | `4.0.2 Web3 签核与 autopilot` + runtime / validation source | - |
| `manual-ceo-signoff` 保留 | `CTO-Signing-Release-Contract` | pending | pending | pending | pending | `4.0.2 Web3 签核与 autopilot` + runtime / validation source | - |
| simulated wallet 的签名原则 | `CTO-Signing-Release-Contract` | pending | pending | pending | pending | `4.0.2 Web3 签核与 autopilot` + runtime / validation source | - |
| default seed / mnemonic 细节 | `CTO-Signing-Release-Contract` | pending | pending | pending | pending | `长期清单 / proving-ground / 下一轮 backlog` | - |
| `Deployment / Assurance` 分层 | `CTO-Evidence-Policy-Contract` | pending | pending | pending | pending | `4. IPD 主动交付线` + runtime / validation source | - |
| local-only deployment strategy 细节 | `CTO-Evidence-Policy-Contract` | pending | pending | pending | pending | `长期清单 / proving-ground / 下一轮 backlog` | - |

## 6. `CEOChiefOfStaff` 汇总回写模板

### 6.1 主流程回写记录

| 项目 | 来源岗位 | merge hook | 是否已回写 | 目标文件 | 落点 | 回写时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | pending | [integrated-product-development-flow.md](integrated-product-development-flow.md) | - | - | - |

### 6.2 runtime / validation 双写记录

| 项目 | 来源岗位 | merge hook | runtime 已回写 | validation 已回写 | 目标文件 | 回写时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| - | - | - | pending | pending | [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) / [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) | - | - |

### 6.3 冻结回流记录

| 项目 | 来源岗位 | merge hook | 是否已回流长期清单 | 是否已进入下一轮 backlog | operating record 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| - | - | - | pending | pending | pending | - |

## 7. 最小验证记录模板

| 验证动作 | 结果 | 执行时间 | 备注 |
| --- | --- | --- | --- |
| 审批稿 Markdown 诊断 | pending | - | - |
| 长期清单 Markdown 诊断 | pending | - | - |
| 主流程真源 Markdown 诊断 | pending | - | - |
| runtime Python 诊断 | pending | - | 仅在有 runtime 改动时填写 |
| validation Python 诊断 | pending | - | 仅在有 validation 改动时填写 |
| operating record Markdown / JSON 诊断 | pending | - | - |

## 8. 批次完成判定

当以下项目全部填完后，可把 `batchStatus` 从 `pending` 改为 `completed`：

1. `CPO` 与 `CTO` 真实回填记录完整。
2. 所有通过项都已记入主流程回写记录或 runtime 双写记录。
3. 所有冻结项都已记入冻结回流记录。
4. 最小验证记录完成。
5. operating record 与 machine object 已同步。

## 9. Guardrails

1. 不得在本模板中预填伪造审批结论。
2. 不得在 `mergeReady = no` 时把项目写成“已回写主流程”。
3. 不得跳过 runtime / validation 双写记录。
4. 不得把当前批次写成 `TriMC` 正式宿主 contract 生效记录。

## 10. Evidence Surface

- [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
- [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
- [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
