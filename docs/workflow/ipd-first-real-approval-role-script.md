# IPD 第一次真实审批回填角色脚本

版本：V0.1
日期：2026-06-15
状态：按岗位的一页式操作稿

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-first-real-approval-role-script.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首次真实审批回填完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文不重复解释 IPD，也不替代 runbook。

它只给三类角色各一段最短操作脚本，目标是在第一次真实审批回填当天，减少在多份文档之间来回切换的认知负担。

## 2. `ChiefProductOfficer` 脚本

1. 打开 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)。
2. 先看 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 里的 `CPO` through-pass 项。
3. 在 `12.1` 填：`reviewStatus`、`reviewedAt`、`decisionSummary`。
4. 在 `12.2` 先填首批 through-pass 项的 `最终决定`，再填其余项目。
5. 在 `12.4` 填：`reviewerDecision`、`signoffRecordedAt`、`mergeReady`。
6. 完成后，回到 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `4.1` 与 `4.2` 同步同样结果。

## 3. `ChiefTechnologyOfficer` 脚本

1. 打开 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)。
2. 先看 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 里的 `CTO` through-pass 项。
3. 在 `13.1` 填：`reviewStatus`、`reviewedAt`、`decisionSummary`。
4. 在 `13.2` 先填首批 through-pass 项的 `最终决定`，再填其余项目。
5. 在 `13.4` 填：`reviewerDecision`、`signoffRecordedAt`、`mergeReady`。
6. 完成后，回到 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `5.1`、`5.2` 与 `6.2` 同步结果。

## 4. `CEOChiefOfStaff` 脚本

1. 打开 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)。
2. 先填写 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `batchStartedAt`、`currentOperator`、`currentStep` 与 `3.1 预启动执行单`。
3. 再检查 `CPO / CTO` 两份审批稿是否都已不再是 `pending`。
4. 按 [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md) 先完成首批 through-pass。
5. 再按 [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md) 处理其余通过项。
6. 把 `FREEZE / REVISE` 项写入 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 承接面与下一轮 backlog。
7. 最后补齐 [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md) 的 `6.1`、`6.2`、`6.3` 与 `7`，并同步 operating record。

## 5. 禁止动作

1. `CEOChiefOfStaff` 不得代填 `CPO / CTO` 的真实审批结论。
2. 未出现 `APPROVE + mergeReady = yes` 时，不得回写主流程真源。
3. 需要 runtime / validation 双写的项目，不得只改文档。
4. 不得把此次回填写成 `TriMC` 正式宿主或生产级 contract 已完成。

## 6. Evidence Surface

- [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
- [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
- [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
- [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
- [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
- [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)
