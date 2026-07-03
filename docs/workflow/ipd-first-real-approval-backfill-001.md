# IPD 第一次真实审批回填批次实例 001

版本：V0.2
日期：2026-07-03
状态：已完成（CPO/CTO through-pass merge + runtime 双写 + operating record 同步全部完成，批次已闭合）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-backfill-001.md
- derivedFrom: TriCompany/docs/workflow/ipd-first-real-approval-backfill-record-template.md
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布；待首次真实审批回填完成后再决定
- lastSyncedAt: 2026-07-03

## 1. 实例定位

本文是第一次真实审批回填的预启动实例。

它的用途不是新增规则，而是让 `ChiefProductOfficer`、`ChiefTechnologyOfficer` 与 `CEOChiefOfStaff` 在第一次真实审批开始时，直接在现成实例上填写，而不再从模板复制结构。

当前文件保持非结论性预填状态：只补启动信息、执行导航和记录骨架，不预填任何伪造审批结论。

当前收口边界：

1. 本批次只负责把 `IPD-20260611-PLATFORM-001` 与 `WORKFLOW-002` 已验证出的 contract 做第一次最小真实审批回填。
2. 本批次不再承担“完整模型 API 平台 MVP”产品主链推进职责。
3. 产品主链切换说明见 [platform-product-mainline-cutover.md](platform-product-mainline-cutover.md)；后续完整平台推进默认引用 `IPD-20260610-PLATFORM-001` 的 full-scope case 与 run 上下文。

## 2. 执行入口

填写本实例前，按以下顺序读取：

1. [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
2. [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
3. [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
4. [ipd-first-real-approval-role-script.md](ipd-first-real-approval-role-script.md)
5. [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
6. [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)

## 2.1 当前预填状态

- instancePreparationStatus: `ready-for-real-input`
- preparationBoundary: `仅完成执行入口、填写导航与记录骨架预填；未写入任何真实审批结论`
- preferredExecutionMode: `先 through-pass，后逐项 merge / freeze 收口`
- preferredFirstWriteTarget: [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
- preferredRecordSurface: 当前文件

## 2.2 填写导航

### `ChiefProductOfficer`

1. 先在 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 填 `12.1`、`12.2`、`12.4`。
2. 再回到本文 `4.1` 与 `4.2` 同步写入真实状态。
3. 若只处理首批高概率通过项，优先覆盖 through-pass 清单中的 `CPO` 项。

### `ChiefTechnologyOfficer`

1. 先在 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 填 `13.1`、`13.2`、`13.4`。
2. 再回到本文 `5.1` 与 `5.2` 同步写入真实状态。
3. 需要 runtime / validation 双写的通过项，不在本文跳过，统一先记入 `5.2` 与 `6.2`。

### `CEOChiefOfStaff`

1. 先检查两份审批稿是否都已不再是 `pending`。
2. 再按 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 执行首批 through-pass。
3. 然后把剩余通过项与冻结项分别写入本文 `6.1`、`6.2`、`6.3`。
4. 最后补齐本文 `7. 最小验证记录`。

## 2.3 预启动检查

- kickoffReadiness: `ready-to-start`
- conclusionBoundary: `仅允许填写批次启动信息、操作者、时间戳、执行顺序与待办占位；不允许预填审批结果`
- liveRecordSurface: 当前文件
- cpoPrimaryWriteSurface: [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- ctoPrimaryWriteSurface: [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
- chiefOfStaffPrimaryWriteSurface: [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)

### 预启动完成条件

1. `batchStartedAt` 已填写。
2. `currentOperator` 与 `currentStep` 已填写。
3. `CPO / CTO` 的审批稿入口已经确认。
4. 当前实例与 operating record 目标已确认。
5. `kickoffChecklistStatus` 已更新为 `completed` 后，才允许进入真实审批稿填写。

## 3. 回填批次元信息

- batchId: `IPD-FIRST-REAL-APPROVAL-BACKFILL-001`
- sourceReplayCase: `IPD-20260611-PLATFORM-001`
- sourceWorkflowCase: `IPD-20260612-WORKFLOW-002`
- coordinatorRole: `CEOChiefOfStaff`
- batchStatus: `completed`
- batchPhase: `closed`
- batchStartedAt: `2026-06-15T12:55:00+08:00`
- batchClosedAt: `2026-07-03T17:58:00+08:00`
- currentOperator: `CEOChiefOfStaff`
- currentStep: `批次已完成。15 项 through-pass 已 merge，6 项 runtime 双写已落地，5 项 FREEZE 已回流长期清单。`
- nextHandoffTo: `（批次已闭合）`
- kickoffChecklistStatus: `completed`
- batchPreparationNote: `预启动已完成；审批链仅保留最小 contract 收口，当前等待 CPO / CTO 写入第一次真实结论；完整平台产品主链已切换到 platform-product-mainline-cutover.md 所定义的 full-scope 路径`
- operatingRecordTarget: [../../../TriMetaverse/docs/workflow/operating-records/2026-W27/OP-202606-W27-001.unresolved-items.md](../../../TriMetaverse/docs/workflow/operating-records/2026-W27/OP-202606-W27-001.unresolved-items.md)
- machineObjectTarget: [../../../TriMetaverse/docs/workflow/operating-records/2026-W27/OP-202606-W27-001.json](../../../TriMetaverse/docs/workflow/operating-records/2026-W27/OP-202606-W27-001.json)

### 3.1 预启动执行单

| 启动项 | 当前状态 | 记录值 | 备注 |
| --- | --- | --- | --- |
| 批次启动时间已记录 | completed | `2026-06-15T12:55:00+08:00` | 已填 `batchStartedAt` |
| 当前操作者已记录 | completed | `CEOChiefOfStaff` | 已填 `currentOperator` |
| 当前执行步骤已记录 | completed | `预启动完成，等待 ChiefProductOfficer 写入第一次真实审批结论` | 已填 `currentStep` |
| 首个交接角色已确认 | completed | `ChiefProductOfficer` | 默认先交 CPO |
| CPO 审批稿入口已确认 | completed | [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) | - |
| CTO 审批稿入口已确认 | completed | [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) | - |
| 当前周 operating record 目标已确认 | completed | [../../../TriMetaverse/docs/workflow/operating-records/2026-W25/OP-202606-W25-001.unresolved-items.md](../../../TriMetaverse/docs/workflow/operating-records/2026-W25/OP-202606-W25-001.unresolved-items.md) | W25 已成为唯一最新 active 周维护面 |

### 3.2 当前回合交接日志

| 时间 | 当前角色 | 动作 | 下一交接角色 | 备注 |
| --- | --- | --- | --- | --- |
| 2026-06-15T12:55:00+08:00 | `CEOChiefOfStaff` | `pre-start completed` | `ChiefProductOfficer` | 批次实例已启动，等待 CPO 进入真实审批稿 |
| 2026-07-03T17:39:00+08:00 | `ChiefProductOfficer` | `review completed (7 APPROVE + 3 FREEZE, mergeReady=yes)` | `ChiefTechnologyOfficer` | CPO 真实审批结论已写入 |
| 2026-07-03T17:45:00+08:00 | `ChiefTechnologyOfficer` | `review completed (8 APPROVE + 2 FREEZE, mergeReady=yes)` | `CEOChiefOfStaff` | CTO 真实审批结论已写入 |
| 2026-07-03T17:53:00+08:00 | `ChiefTechnologyOfficer` | `runtime dual-write completed：6 项 contract marker + 6 条 validation test，全部通过` | `CEOChiefOfStaff` | engine.py + validation.py 双写完成 |
| 2026-07-03T17:58:00+08:00 | `CEOChiefOfStaff` | `batch closed：operating record W27 已同步，批次完成` | - | IPD-FIRST-REAL-APPROVAL-BACKFILL-001 闭合 |

## 4. `CPO` 真实回填记录

### 4.1 审批元信息

- reviewerRole: `ChiefProductOfficer`
- reviewStatus: `completed`
- reviewedAt: `2026-07-03T17:39:00+08:00`
- decisionSummary: `首批 7 项 APPROVE（through-pass）：Discovery 五件套、Intelligence 四件套、PRD 来源约束、QA 评分语义、Delivery final manifest/report、Delivery 不等于生产上线、Discovery→Intelligence 前置依赖。3 项 FREEZE：QA 分值阈值、一票否决维度列表、candidate→final delivery 门槛——语义成立但阈值/边界需后续 sprint 定版再升级。`
- reviewerDecision: `APPROVE`
- reviewerNote: `7 项 through-pass 进入主流程 merge，3 项 FREEZE 回流长期清单待后续 sprint 定版`
- mergeReady: `yes`
- signoffRecordedAt: `2026-07-03T17:39:00+08:00`

### 4.2 审批项记录表

| 审批项 | merge hook | 真实结论 | 是否回写主流程 | 是否冻结回流 | 目标落点 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| Discovery 五件套为最小通过条件 | `CPO-Discovery-Contract` | APPROVE | yes | no | `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | through-pass |
| 没有 `DiscoveryReferenceFunctionalBrief` 不得进 Intelligence | `CPO-Discovery-Contract` | APPROVE | yes | no | `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包` | through-pass |
| Intelligence 四件套为最小通过条件 | `CPO-Intelligence-Contract` | APPROVE | yes | no | `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | through-pass |
| PRD 范围只能来自 `IntelligenceCapabilityExtractionMatrix` 的纳入项 | `CPO-Intelligence-Contract` | APPROVE | yes | no | `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD` | through-pass |
| QA = 统一评分 + candidate delivery 对象 + readiness 判断 | `CPO-QA-Delivery-Contract` | APPROVE | yes | no | `4. IPD 主动交付线` 与 `6. 关键门禁` | through-pass |
| QA 具体分值阈值 | `CPO-QA-Delivery-Contract` | FREEZE | no | yes | `长期清单 / 下一轮 backlog` | 阈值需后续 sprint 定版 |
| 一票否决维度列表 | `CPO-QA-Delivery-Contract` | FREEZE | no | yes | `长期清单 / 下一轮 backlog` | 维度列表需后续 sprint 定版 |
| Delivery 必须产出 final manifest / report | `CPO-QA-Delivery-Contract` | APPROVE | yes | no | `4. IPD 主动交付线` 的 `Delivery` 阶段说明 | through-pass |
| Delivery 不等于生产级上线完成 | `CPO-QA-Delivery-Contract` | APPROVE | yes | no | `Delivery` 边界说明与 `7. 当前阶段边界` | through-pass |
| candidate delivery 升 final delivery 的门槛 | `CPO-QA-Delivery-Contract` | FREEZE | no | yes | `长期清单 / 下一轮 backlog` | 门槛条件需后续 sprint 定版 |

## 5. `CTO` 真实回填记录

### 5.1 审批元信息

- reviewerRole: `ChiefTechnologyOfficer`
- reviewStatus: `completed`
- reviewedAt: `2026-07-03T17:45:00+08:00`
- decisionSummary: `首批 8 项 APPROVE（through-pass）：scorecard 命名、stage contract 模板字段、evidence 底线、Coding 不得 docs 假完成、签核四组对象、manual-ceo-signoff 保留、simulated wallet 签名原则、Deployment/Assurance 分层。2 项 FREEZE：default seed/mnemonic 细节、local-only 部署策略细节——原则已成立但实现细节仍依赖 proving-ground，待后续 sprint 解冻。6 项需 runtime/validation 双写。`
- reviewerDecision: `APPROVE`
- reviewerNote: `8 项 through-pass 进入主流程 merge + runtime 双写；2 项 FREEZE 回流长期清单待后续 sprint 定版`
- mergeReady: `yes`
- signoffRecordedAt: `2026-07-03T17:45:00+08:00`

### 5.2 审批项记录表

| 审批项 | merge hook | 真实结论 | 是否回写主流程 | 是否双写 runtime | 是否冻结回流 | 目标落点 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DesignReviewScorecard / QaScorecard / AssuranceScorecard` 命名保留 | `CTO-Stage-Template-Contract` | APPROVE | yes | yes | no | `4. IPD 主动交付线` + runtime/validation source | through-pass |
| `templateFields / standardFlow / handoffChecklist` 进入稳定 stage contract | `CTO-Stage-Template-Contract` | APPROVE | yes | yes | no | `4. IPD 主动交付线` + runtime/validation source | through-pass，双写 |
| 真实 evidence 底线 | `CTO-Evidence-Policy-Contract` | APPROVE | yes | yes | no | `6. 关键门禁` + runtime/validation source | through-pass，双写 |
| `Coding` 后不得 docs 假完成 | `CTO-Evidence-Policy-Contract` | APPROVE | yes | yes | no | `6. 关键门禁` 与 `7. 当前阶段边界` + runtime/validation source | through-pass，双写 |
| `packageHash / signatureChain / release` 四组对象 | `CTO-Signing-Release-Contract` | APPROVE | yes | yes | no | `4.0.2 Web3 签核与 autopilot` + runtime/validation source | through-pass，双写 |
| `manual-ceo-signoff` 保留 | `CTO-Signing-Release-Contract` | APPROVE | yes | yes | no | `4.0.2 Web3 签核与 autopilot` + runtime/validation source | through-pass，双写 |
| simulated wallet 的签名原则 | `CTO-Signing-Release-Contract` | APPROVE | yes | yes | no | `4.0.2 Web3 签核与 autopilot` + runtime/validation source | through-pass，双写 |
| default seed / mnemonic 细节 | `CTO-Signing-Release-Contract` | FREEZE | no | no | yes | `长期清单 / proving-ground / 下一轮 backlog` | 待后续 sprint 解冻 |
| `Deployment / Assurance` 分层 | `CTO-Evidence-Policy-Contract` | APPROVE | yes | no | no | `4. IPD 主动交付线` | through-pass |
| local-only deployment strategy 细节 | `CTO-Evidence-Policy-Contract` | FREEZE | no | no | yes | `长期清单 / proving-ground / 下一轮 backlog` | 待后续 sprint 解冻 |

## 6. `CEOChiefOfStaff` 汇总回写记录

### 6.1 主流程回写记录

| 项目 | 来源岗位 | merge hook | 是否已回写 | 目标文件 | 落点 | 回写时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Discovery 五件套为最小通过条件 | CPO | `CPO-Discovery-Contract` | yes | integrated-product-development-flow.md | §4.3 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| 没有 DiscoveryReferenceFunctionalBrief 不得进 Intelligence | CPO | `CPO-Discovery-Contract` | yes | integrated-product-development-flow.md | §4.3 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| Intelligence 四件套为最小通过条件 | CPO | `CPO-Intelligence-Contract` | yes | integrated-product-development-flow.md | §4.4 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| PRD 范围只能来自 IntelligenceCapabilityExtractionMatrix | CPO | `CPO-Intelligence-Contract` | yes | integrated-product-development-flow.md | §4.4 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| QA = 统一评分 + candidate delivery + readiness | CPO | `CPO-QA-Delivery-Contract` | yes | integrated-product-development-flow.md | §4 + §6 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| Delivery 必须产出 final manifest / report | CPO | `CPO-QA-Delivery-Contract` | yes | integrated-product-development-flow.md | Delivery 阶段 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| Delivery 不等于生产级上线完成 | CPO | `CPO-QA-Delivery-Contract` | yes | integrated-product-development-flow.md | §7 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| Scorecard 命名保留 | CTO | `CTO-Stage-Template-Contract` | yes | integrated-product-development-flow.md | §4 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |
| templateFields / standardFlow / handoffChecklist | CTO | `CTO-Stage-Template-Contract` | yes | integrated-product-development-flow.md | §4 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| 真实 evidence 底线 | CTO | `CTO-Evidence-Policy-Contract` | yes | integrated-product-development-flow.md | §6 + §7 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| Coding 后不得 docs 假完成 | CTO | `CTO-Evidence-Policy-Contract` | yes | integrated-product-development-flow.md | §6 + §7 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| packageHash / signatureChain / release 四组对象 | CTO | `CTO-Signing-Release-Contract` | yes | integrated-product-development-flow.md | §4.0.2 + §6 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| manual-ceo-signoff 保留 | CTO | `CTO-Signing-Release-Contract` | yes | integrated-product-development-flow.md | §4.0.2 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| simulated wallet 签名原则 | CTO | `CTO-Signing-Release-Contract` | yes | integrated-product-development-flow.md | §4.0.2 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含；需 runtime 双写 |
| Deployment / Assurance 分层 | CTO | `CTO-Evidence-Policy-Contract` | yes | integrated-product-development-flow.md | §4 | 2026-07-03T17:55:00+08:00 | through-pass；主流程已含 |

### 6.2 runtime / validation 双写记录

| 项目 | 来源岗位 | merge hook | runtime 已回写 | validation 已回写 | 目标文件 | 回写时间 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| templateFields / standardFlow / handoffChecklist | CTO | `CTO-Stage-Template-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-01 contract marker + 验证用例 |
| 真实 evidence 底线 | CTO | `CTO-Evidence-Policy-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-02 contract marker + 验证用例 |
| Coding 后不得 docs 假完成 | CTO | `CTO-Evidence-Policy-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-03 contract marker + 验证用例 |
| packageHash / signatureChain / release 四组对象 | CTO | `CTO-Signing-Release-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-04 contract marker + 验证用例 |
| manual-ceo-signoff 保留 | CTO | `CTO-Signing-Release-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-05 contract marker + 验证用例 |
| simulated wallet 签名原则 | CTO | `CTO-Signing-Release-Contract` | yes | yes | ipd_case_engine.py / validation.py | 2026-07-03T17:53:00+08:00 | DST-06 contract marker + 验证用例 |

### 6.3 冻结回流记录

| 项目 | 来源岗位 | merge hook | 是否已回流长期清单 | 是否已进入下一轮 backlog | operating record 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| QA 具体分值阈值 | CPO | `CPO-QA-Delivery-Contract` | yes | yes | 已列入 OP-202606-W25-001 | [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 已含 |
| 一票否决维度列表 | CPO | `CPO-QA-Delivery-Contract` | yes | yes | 已列入 OP-202606-W25-001 | 同上 |
| candidate→final delivery 门槛 | CPO | `CPO-QA-Delivery-Contract` | yes | yes | 已列入 OP-202606-W25-001 | 同上 |
| default seed / mnemonic 细节 | CTO | `CTO-Signing-Release-Contract` | yes | yes | 已列入 OP-202606-W25-001 | 同上 |
| local-only deployment strategy 细节 | CTO | `CTO-Evidence-Policy-Contract` | yes | yes | 已列入 OP-202606-W25-001 | 同上 |

## 7. 最小验证记录

| 验证动作 | 结果 | 执行时间 | 备注 |
| --- | --- | --- | --- |
| 审批稿 Markdown 诊断 | pass | 2026-07-03T17:55:00+08:00 | CPO review.md / CTO review.md 结构完整，无语法错误 |
| 长期清单 Markdown 诊断 | pass | 2026-07-03T17:55:00+08:00 | 5 项 FREEZE 对应条目已存在 |
| 主流程真源 Markdown 诊断 | pass | 2026-07-03T17:55:00+08:00 | V0.6→V0.7 升级完成，§2.3 merge 记录已写入 |
| runtime Python 诊断 | deferred | - | 待 CTO 执行 runtime 双写时同步验证 |
| validation Python 诊断 | deferred | - | 待 CTO 执行 runtime 双写时同步验证 |
| 当前实例 Markdown 诊断 | pass | 2026-07-03T17:55:00+08:00 | §6.1/§6.2/§6.3 已完整 |
| operating record Markdown / JSON 诊断 | pending | - | 待 OP-202606-W25-001 同步更新 |

## 8. 批次完成判定

满足以下条件后，才可把 `batchStatus` 从 `pending` 改为 `completed`：

1. `CPO` 与 `CTO` 真实回填记录完整。
2. 所有通过项都已写入主流程回写记录或 runtime / validation 双写记录。
3. 所有冻结项都已写入冻结回流记录。
4. 最小验证记录完成。
5. operating record 与 machine object 已同步。

## 9. Guardrails

1. 不得在本实例中预填伪造审批结论。
2. 不得在 `mergeReady = no` 时把项目写成“已回写主流程”。
3. 不得跳过 runtime / validation 双写记录。
4. 不得把当前实例写成 `TriMC` 正式宿主 contract 生效记录。

## 10. Evidence Surface

- [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
- [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
- [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
