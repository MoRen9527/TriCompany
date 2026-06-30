# IPD-20260612-WORKFLOW-002 Approval Backfill Rehearsal

## Rehearsal Boundary

- 本文件是 `WORKFLOW-002` 在 validation-handoff 之后追加的一次准真实审批回填演练。
- 它只验证“审批项 -> merge hook -> 主流程回写 / 冻结回流”两条路径是否清晰可执行。
- 它不是 `ChiefProductOfficer` 或 `ChiefTechnologyOfficer` 的真实审批结论，不回写真实审批稿，不替代正式签发。

## Rehearsal Goal

本次演练只验证四类代表性场景：

1. `CPO` 的 `APPROVE + mergeReady = yes` 如何回写主流程真源。
2. `CPO` 的 `FREEZE + mergeReady = no` 如何继续回流到总清单与下一轮 backlog。
3. `CTO` 的 `APPROVE + mergeReady = yes` 如何同时指向主流程真源与 runtime / validation 双写。
4. `CTO` 的 `FREEZE + mergeReady = no` 如何继续留在 proving-ground / workflow backlog 层。

## Rehearsal Scenarios

### 1. CPO approve 路径样例

- rehearsalItem: `Discovery 五件套为最小通过条件`
- sourceReviewFile: [../../ipd-product-acceptance-contract-cpo-review.md](../../ipd-product-acceptance-contract-cpo-review.md)
- mergeHook: `CPO-Discovery-Contract`
- simulatedDecision: `APPROVE`
- simulatedMergeReady: `yes`
- expectedWritebackTarget: [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)
- expectedLandingZone: `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包`
- expectedOutcome: 主流程真源可以直接吸收该条最小通过条件，无需先进入冻结池。

### 2. CPO freeze 路径样例

- rehearsalItem: `QA 具体分值阈值`
- sourceReviewFile: [../../ipd-product-acceptance-contract-cpo-review.md](../../ipd-product-acceptance-contract-cpo-review.md)
- mergeHook: `CPO-QA-Delivery-Contract`
- simulatedDecision: `FREEZE`
- simulatedMergeReady: `no`
- expectedWritebackTarget: [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)
- expectedLandingZone: `需要 CPO 固化的产品 / 验收 Contract` 与下一轮 workflow backlog seeds
- expectedOutcome: 该项不进入主流程真源，而是保留在长期清单并进入下一轮 backlog。

### 3. CTO approve 路径样例

- rehearsalItem: ``packageHash / signatureChain / release`` 四组对象
- sourceReviewFile: [../../ipd-runtime-evidence-contract-cto-review.md](../../ipd-runtime-evidence-contract-cto-review.md)
- mergeHook: `CTO-Signing-Release-Contract`
- simulatedDecision: `APPROVE`
- simulatedMergeReady: `yes`
- expectedWritebackTarget: [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)、[../../../runtime/cognition/ipd_case_engine.py](../../../runtime/cognition/ipd_case_engine.py)、[../../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
- expectedLandingZone: `4.0.2 Web3 签核与 autopilot` 与对应 runtime / validation source
- expectedOutcome: 该项需要文档真源与执行真源双写，不允许只改文档不改 runtime。

### 4. CTO freeze 路径样例

- rehearsalItem: `default seed / mnemonic 细节`
- sourceReviewFile: [../../ipd-runtime-evidence-contract-cto-review.md](../../ipd-runtime-evidence-contract-cto-review.md)
- mergeHook: `CTO-Signing-Release-Contract`
- simulatedDecision: `FREEZE`
- simulatedMergeReady: `no`
- expectedWritebackTarget: [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)
- expectedLandingZone: `当前应继续冻结在 proving-ground 层的项目` 与下一轮 workflow backlog seeds
- expectedOutcome: 该项继续保留在 proving-ground / workflow backlog，不进入常态 runtime contract。

## Rehearsal Result

本轮演练验证出以下结论：

1. `APPROVE + mergeReady = yes` 的路由已经足够明确，可以直接映射到主流程真源的指定 merge hook。
2. 涉及技术 contract 的 `APPROVE` 项，不应只回写主流程文档，必须同时指向 runtime / validation 双写。
3. `FREEZE + mergeReady = no` 的路由已经明确回到长期固化清单与下一轮 workflow backlog，而不是滞留在审批稿内。
4. 当前缺口不再是路由不清，而是真实岗位审批尚未填写。

## Follow-Up After Rehearsal

### 1. 真实审批前保持不变的事项

- 当前 `CPO / CTO` 审批稿继续保持 `pending`。
- 当前演练结果不覆盖审批稿中的 `最终决定` 字段。
- 当前演练结果不触发对主流程真源或 runtime source 的实际语义改写。

### 2. 真实审批开始后应立即执行的动作

- 把真实 `APPROVE + mergeReady = yes` 的项目按相同路径回写。
- 把真实 `FREEZE / REVISE` 项同步回写到长期固化清单，并转成下一轮 backlog seeds。
- 对需要双写的技术项，确保主流程真源、runtime source、validation source 同轮或下一轮收口。
- 首批高概率通过项，先按 [../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md) 执行短版 through-pass。
- 本轮真实回填统一以 [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md) 为填写面，并以 [../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md) 作为其余 through-pass 之后的逐项 landing zone 依据。

## Guardrails

- 不得把本演练写成 `CPO / CTO` 已完成正式审批。
- 不得把本演练写成主流程真源或 runtime source 已经按真实审批升级。
- 不得把当前本地 Copilot-host 正式接管阶段的演练闭环，写成 TriMC 正式宿主或生产级 contract 已完成。

## Evidence Surface

- [06-validation-handoff-plan.md](06-validation-handoff-plan.md)
- [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)
- [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)
- [../../ipd-product-acceptance-contract-cpo-review.md](../../ipd-product-acceptance-contract-cpo-review.md)
- [../../ipd-runtime-evidence-contract-cto-review.md](../../ipd-runtime-evidence-contract-cto-review.md)
- [../../ipd-first-real-approval-backfill-runbook.md](../../ipd-first-real-approval-backfill-runbook.md)
- [../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md)
- [../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md)
- [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md)
