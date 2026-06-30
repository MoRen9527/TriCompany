# Discovery Replay 验证角色脚本

版本：V0.1
日期：2026-06-16
状态：按岗位的一页式操作稿

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/agile-improvement/IPD-20260612-WORKFLOW-002/11-discovery-replay-role-script.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待首轮 replay 验证完成后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-16

## 1. 文档定位

本文不重复解释 carry-forward guard，也不替代 checklist / package / 结果模板。

它只给三类角色各一段最短操作脚本，目标是在首轮 `Discovery replay` 验证当天，减少在多份文档之间来回切换的认知负担。

## 2. `ChiefTechnologyOfficer` 脚本

1. 打开 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)。
2. 先填 `3. 自测批次元信息` 的 `startedAt`。
3. 再填 `4. 实现范围记录` 的 `implementationSummary`、`touchedFiles`、`validationPathSummary`。
4. 逐步执行 `6. 自测步骤记录表`，补齐 `实际结果`、`是否通过`、`备注`。
5. 在 `7. 自测结论` 填 `selfTestSummary`、`observedGaps`、`passDecision`、`replayReadyDecision`、`replayReadyNote`。
6. 完成后，把实例交回 `CEOChiefOfStaff`，等待确认是否允许 `CPO` 开始 replay。

若当前结论仍是 `partial-pass / replayReady=no`，下一步直接参考 [12-sp202a-cto-implementation-task-sheet.md](12-sp202a-cto-implementation-task-sheet.md) 继续改代码，而不是口头宣布可 replay。

若 `10-discovery-replay-result-001.md` 的真实结果已经是 `revision-required`，说明最小 guard 已过，但 replay 正文仍未追平 baseline；此时不要回到 `SP-202A` 重新争论是否可 replay，直接参考 [13-discovery-replay-revision-follow-up-task-sheet.md](13-discovery-replay-revision-follow-up-task-sheet.md) 进入下一轮 CTO 修复。

## 3. `ChiefProductOfficer` 脚本

1. 先确认 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md) 的 `replayReadyDecision` 已不再是 `pending`。
2. 打开 [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)。
3. 填 `3. Replay 批次元信息` 的 `startedAt`。
4. replay 完成后，先填 `5. Replay 输出记录` 的输出路径与 `additionalCompetitorsObserved`。
5. 再填 `7. 差异与结论` 的 `cpoDisposition` 与必要 `replayNotes`。
6. 完成后，把实例交回 `CEOChiefOfStaff` 做 seeded competitor 覆盖核对与最终处置。

若 replay 结果为 `revision-required` 且原因是正文质量回退，不要把它误判成 carry-forward guard 失败；应把结果交回 `ChiefTechnologyOfficer`，按 [13-discovery-replay-revision-follow-up-task-sheet.md](13-discovery-replay-revision-follow-up-task-sheet.md) 修补 Discovery 自动化输出质量。

## 4. `CEOChiefOfStaff` 脚本

1. 先检查 [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md) 是否已经给出 `replayReadyDecision`。
2. 若未 ready，不允许 `CPO` 开始 replay。
3. 若已 ready，再检查 [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md) 的 `replayCatalogRef`、`replayBriefRef`、`replayLandscapeRef` 是否已填写。
4. 在 `6. Seeded Competitor 覆盖结果表` 逐项核对 `LiteLLM`、`sub2api`、`OpenRouter`、`OpenAI API Platform`。
5. 在 `7. 差异与结论` 填 `comparisonSummary`、`missingCompetitors`、`chiefOfStaffDisposition`、`finalDispositionReason`。
6. 最后补 `8. 最小验证记录`，再决定是 `pass`、`revision-required` 还是 `blocked`。

## 5. 禁止动作

1. `CEOChiefOfStaff` 不得代填 `CTO` 的 guard 自测结论。
2. `CEOChiefOfStaff` 不得代填 `CPO` 的 replay 产品侧结论。
3. `CPO` 不得在 `CTO` 未给出 `replayReadyDecision` 前直接开始 replay。
4. 任何角色都不得把“新增更多竞品”写成 seeded competitors 丢失的豁免理由。
5. 不得把 replay 通过写成 20260610 case 已完成生产级发布。

## 6. Evidence Surface

- [08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md)
- [08-discovery-replay-validation-package.json](08-discovery-replay-validation-package.json)
- [09-cto-focused-self-test-001.md](09-cto-focused-self-test-001.md)
- [10-discovery-replay-result-001.md](10-discovery-replay-result-001.md)
- [12-sp202a-cto-implementation-task-sheet.md](12-sp202a-cto-implementation-task-sheet.md)
- [13-discovery-replay-revision-follow-up-task-sheet.md](13-discovery-replay-revision-follow-up-task-sheet.md)
