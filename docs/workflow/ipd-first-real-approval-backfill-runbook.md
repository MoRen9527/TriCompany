# IPD 第一次真实审批回填执行手册

版本：V0.1
日期：2026-06-15
状态：当前 Copilot-host live 阶段可执行 runbook

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-backfill-runbook.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待当前 runbook 在真实审批中使用后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文只解决一个问题：当 `IPD-20260611-PLATFORM-001` 的 proving-ground replay、`WORKFLOW-002` 的 source-side 闭环和 `07-approval-backfill-rehearsal` 都已经准备好后，`CPO / CTO / CEOChiefOfStaff` 第一次真实审批回填应当如何执行。

它不是审批结论本身，也不代替 `CPO` 或 `CTO` 的专业判断。它只定义操作顺序、回填位置、merge hook 对应关系、冻结回流路径和最小验证动作。

## 2. 前置核查

开始真实审批前，先核查以下真源和入口是否已就绪：

1. 主流程真源：[integrated-product-development-flow.md](integrated-product-development-flow.md)
2. 总清单：[ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
3. `CPO` 审批稿：[ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
4. `CTO` 审批稿：[ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
5. merge 候选矩阵：[ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
6. 批次记录模板：[ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md)
7. through-pass 短版执行单：[ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
8. 空白批次实例：[ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
9. 角色脚本：[ipd-first-real-approval-role-script.md](ipd-first-real-approval-role-script.md)
10. 演练样本：[agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md)
11. 当前 operating record：[../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md](../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md)

只有在以上材料都存在且最近一轮校验通过后，才进入真实审批。

## 3. 角色边界

### 3.1 `ChiefProductOfficer`

- 只审批产品 / 验收 contract。
- 只在 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 填写真实判断。
- 不代替 `CTO` 决定 runtime schema、evidence policy 或签核技术细节。

### 3.2 `ChiefTechnologyOfficer`

- 只审批 runtime / evidence contract。
- 只在 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 填写真实判断。
- 不代替 `CPO` 决定产品范围、QA 分值阈值或 Delivery 完成定义。

### 3.3 `CEOChiefOfStaff`

- 不替两位岗位给审批结论。
- 只负责检查回填完整性、按 merge hook 组织回写、把冻结项转回总清单和 backlog，并同步 operating record。

## 4. 标准执行顺序

第一次真实审批回填固定采用以下顺序：

1. `CEOChiefOfStaff` 先在 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 完成预启动：填写 `batchStartedAt`、`currentOperator`、`currentStep` 与 `3.1 预启动执行单`。
2. `CPO` 填产品 / 验收审批稿，并同步批次实例的 `4.1`、`4.2`。
3. `CTO` 填 runtime / evidence 审批稿，并同步批次实例的 `5.1`、`5.2`。
4. `CEOChiefOfStaff` 检查两份审批稿是否具备 `reviewedAt`、`decisionSummary`、`最终决定`、`reviewerDecision` 和 `mergeReady`。
5. `CEOChiefOfStaff` 先按 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 处理首批 `APPROVE + mergeReady = yes` 项，并立即回写批次实例的 `6.1` / `6.2`。
6. `CEOChiefOfStaff` 再按 [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md) 处理剩余通过项，补齐主流程回写与必要 runtime / validation 双写。
7. `CEOChiefOfStaff` 把真实 `FREEZE / REVISE` 项同步回写到总清单、下一轮 workflow backlog seeds 与批次实例的 `6.3`。
8. 回写完成后，先补批次实例的 `7. 最小验证记录`，再更新 operating record 与 machine object。

## 5. `CPO` 回填步骤

在 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 中按以下顺序操作：

1. 在 `12.1 审批元信息` 填写：
   - `reviewStatus`
   - `reviewedAt`
   - `decisionSummary`
2. 在 `12.2 审批结果表` 中，对每一行填入真实 `最终决定`：
   - `APPROVE`
   - `FREEZE`
   - `REVISE`
3. 在 `12.3 回灌动作` 中只更新真实受影响动作的 `状态`。
4. 在 `12.4 签发区` 中填写：
   - `reviewerDecision`
   - `reviewerNote`
   - `escalationRequired`
   - `followUpSprintNeeded`
   - `signoffRecordedAt`
   - `mergeReady`

`CPO` 审批稿中的 merge hook 对应关系固定为：

- `CPO-Discovery-Contract`
- `CPO-Intelligence-Contract`
- `CPO-QA-Delivery-Contract`

## 6. `CTO` 回填步骤

在 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 中按以下顺序操作：

1. 在 `13.1 审批元信息` 填写：
   - `reviewStatus`
   - `reviewedAt`
   - `decisionSummary`
2. 在 `13.2 审批结果表` 中，对每一行填入真实 `最终决定`。
3. 在 `13.3 回灌动作` 中只更新真实受影响动作的 `状态`。
4. 在 `13.4 签发区` 中填写：
   - `reviewerDecision`
   - `reviewerNote`
   - `escalationRequired`
   - `followUpSprintNeeded`
   - `signoffRecordedAt`
   - `mergeReady`

`CTO` 审批稿中的 merge hook 对应关系固定为：

- `CTO-Stage-Template-Contract`
- `CTO-Evidence-Policy-Contract`
- `CTO-Signing-Release-Contract`

## 7. `CEOChiefOfStaff` 回写步骤

### 7.1 处理 `APPROVE + mergeReady = yes`

只对同时满足以下条件的项目执行回写：

1. 审批稿中的 `最终决定 = APPROVE`
2. 签发区 `mergeReady = yes`
3. 对应 merge hook 已在主流程真源中存在

回写规则：

1. 产品 / 验收项：先回写 [integrated-product-development-flow.md](integrated-product-development-flow.md)
2. 技术 / runtime 项：先回写主流程真源，再回写：
   - [runtime/cognition/ipd_case_engine.py](../runtime/cognition/ipd_case_engine.py)
   - [runtime/cognition/chief_of_staff_ipd_case_validation.py](../runtime/cognition/chief_of_staff_ipd_case_validation.py)
3. 回写后，必须执行最小校验，确认文档与 runtime 没有分叉。

### 7.2 处理 `FREEZE / REVISE`

对以下情况不回写主流程真源：

1. `最终决定 = FREEZE`
2. `最终决定 = REVISE`
3. `mergeReady = no`

这些项目必须：

1. 回写到 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
2. 写入下一轮 `WORKFLOW-002` backlog seed
3. 在 operating record 中记录“仍待联审收口”或“继续冻结”状态

## 8. 最小验证动作

完成第一次真实审批回填后，最小验证固定包括：

1. 审批稿 Markdown 诊断通过。
2. 总清单 Markdown 诊断通过。
3. 主流程真源 Markdown 诊断通过。
4. 若改了 runtime source，则对应 Python 文件诊断通过。
5. 更新后的 operating record Markdown / JSON 诊断通过。

如果存在 runtime source 改动，优先补一条聚焦验证，而不是只看 diff。

## 9. 禁止事项

1. 不得由 `CEOChiefOfStaff` 代替 `CPO / CTO` 填真实审批结论。
2. 不得把 `mergeReady = yes` 但 `最终决定` 非 `APPROVE` 的项目写回主流程真源。
3. 不得跳过 runtime 双写，只改文档真源。
4. 不得把第一次真实审批回填写成“生产级 contract 已全部生效”。
5. 不得把当前阶段写成 `TriMC` 正式宿主已经切换完成。

## 10. 完成定义

满足以下条件，视为“第一次真实审批回填”完成：

1. `CPO` 与 `CTO` 审批稿都已完成真实回填。
2. 所有 `APPROVE + mergeReady = yes` 项都已按 hook 正确回写。
3. 所有 `FREEZE / REVISE` 项都已进入总清单与下一轮 backlog 种子。
4. operating record 与 machine object 已同步。
5. 本轮相关文档与代码校验全部通过。

## 11. Evidence Surface

- [integrated-product-development-flow.md](integrated-product-development-flow.md)
- [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
- [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
- [ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md)
- [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
- [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- [ipd-first-real-approval-role-script.md](ipd-first-real-approval-role-script.md)
- [agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md)
- [../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md](../TriMetaverse/docs/workflow/operating-records/2026-W24/OP-202606-W24-001.unresolved-items.md)
