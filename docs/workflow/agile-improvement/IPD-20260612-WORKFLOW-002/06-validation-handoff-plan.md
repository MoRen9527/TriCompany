# IPD-20260612-WORKFLOW-002 Validation Handoff Plan

## Stabilized Rules

### 1. replay 反整理出来的联审链已经具备固定入口

- `IPD-20260611-PLATFORM-001` 的 proving-ground replay 现在不会只留在 narrative 结论层。
- 已验证候选规则会先进入 [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)，再拆分到 `CPO / CTO` 审批稿。
- 这条“replay -> 总清单 -> 审批稿”路径已经稳定，可作为后续同类流程优化的固定入口。

### 2. 审批结果已经具备稳定 merge 路由

- 主流程真源已预埋 `CPO-*` 与 `CTO-*` merge hook。
- 审批稿回填模板已直接标注对应 hook。
- 后续可按 `APPROVE + mergeReady = yes -> 主流程 / runtime 回写`、`FREEZE / REVISE -> 总清单 / backlog 回流` 两条路径分流。

### 3. 当前阶段必须坚持“先审、再回写、后验证”

- 当前不能因为 merge hook 已经齐备，就跳过真实岗位审批直接改 runtime。
- 对需要双写的项目，必须在真实审批之后，再按主流程文档和 runtime source 同轮或下一轮回写。
- 这条规则应继承到后续任何 IPD contract 固化动作，避免把候选规则提前写成既成事实。

### 4. Discovery competitor carry-forward guard 必须用 replay 验证，而不是口头确认

- `SP-202A` 的验收目标不是“文档里提过这条规则”，而是证明新的 Discovery 自动化在扩展竞品时，仍然会保留 CEO seeded competitors 的后续引用覆盖。
- 因此这条规则的首轮验证必须回到真实 case 的 Discovery 重跑，而不是只做静态审文或人工口头检查。
- 但 replay 必须保留现有 Discovery baseline evidence，避免验证通过后反而丢失“guard 上线前”的对照面。

## Recommended Validation Action

### 1. 建议先做一轮真实审批回填演练

- 建议对象：当前 `CPO` 审批稿与 `CTO` 审批稿。
- 建议目标：验证 `APPROVE / FREEZE / REVISE`、`mergeReady`、merge hook 和 backlog 回流这四组机制是否能在一次真实回填中无缝配合。
- 建议约束：演练只允许写真实岗位判断，不允许为了证明流程可用而伪造批准结论。

### 2. 建议把 Discovery carry-forward guard 先做一轮非破坏性 replay 验证

- 建议对象：`IPD-20260610-PLATFORM-001` 的 Discovery 阶段。
- 建议前提：先由 `CTO` 完成 runtime / validation 侧的 guard 实现与 focused self-test，再由 `CEOChiefOfStaff` 依据验收清单确认 replay ready。
- 建议动作：`CPO` 不直接清空现有 Discovery 产物，而是保留当前 output 作为 baseline，随后基于同一 intake briefing 重走 Discovery，检查 `reference-source-catalog`、`functional-brief`、`competitor-landscape` 是否全部覆盖 seeded competitors。
- 建议判定：如果 replay 结果缺失任何 seeded competitor，则 Discovery 必须标记 `revision-required` 或被阻断；如果 seeded competitors 全部覆盖且允许扩展竞品，则 guard 验收通过。

### 3. 建议把通过项与冻结项分成两条后续路径

- 通过项：回写 [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)，并在需要时同步回写 runtime source。
- 冻结项：继续回写 [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)，并作为下一轮 workflow backlog seeds。

## Handoff Checklist For Next Workflow Step

### 1. 开始真实审批或 Discovery replay 前必须确认的事项

- `CPO` 与 `CTO` 审批稿的回填模板仍保持最新。
- 主流程真源的 merge hook 名称与审批稿中的 hook 名称完全一致。
- 长期固化清单已准备好接住 `FREEZE / REVISE` 项。
- 当前 Discovery baseline evidence 已保留，或已具备先归档再 replay 的路径，不能以直接清空产物代替验证。
- 第一次真实审批回填的执行资产链已经齐备：[../../ipd-first-real-approval-backfill-runbook.md](../../ipd-first-real-approval-backfill-runbook.md)、[../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md)、[../../ipd-first-real-approval-backfill-record-template.md](../../ipd-first-real-approval-backfill-record-template.md)、[../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md) 与 [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md)。

### 2. 真实审批后必须立即执行的动作

- 把 `APPROVE + mergeReady = yes` 的项目按 hook 回写主流程真源。
- 对需要技术双写的通过项，同步安排 runtime source 与 validation source 回写。
- 把 `FREEZE / REVISE` 项整理成下一轮 backlog seeds，而不是留在审批稿里悬空。
- 首批高概率通过项，优先按 [../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md) 执行 through-pass；其余通过项再按 [../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md) 收口。
- 本轮真实记录统一落到 [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md)，不再从模板临时复制结构。

### 3. 明确禁止继承的错误外推

- 不得把“审批稿 ready”写成“审批已完成”。
- 不得把“主流程文档已带 merge hook”写成“runtime source 已自动升级”。
- 不得把当前本地 Copilot-host 正式接管阶段的联审闭环，写成 TriMC 正式宿主或生产级 contract 已完成。
- 不得把“要验证 Discovery guard”理解成“先清空现有 Discovery evidence 再说”；没有 baseline 的重跑，只能证明当前输出，不能证明 guard 提升是否成立。

## Completion Conclusion

- 当前 `WORKFLOW-002` 已完成“长期 contract 联审准备链 + merge 路由”的阶段性固化。
- 到 validation-handoff 为止，这条 case 的职责是确保审批能真实回填、冻结项能真实回流，不直接替代真实岗位审批本身。
- 下一步应先完成 `SP-202A` 的 CTO 实施与总助验收，再进入一次真实审批回填或 Discovery 非破坏性 replay，验证这条 merge / freeze 双分流链和 competitor carry-forward guard 是否可连续运行。
- 当前已补出第一份准真实演练产物：[07-approval-backfill-rehearsal.md](07-approval-backfill-rehearsal.md) 与 [07-approval-backfill-rehearsal-package.json](07-approval-backfill-rehearsal-package.json)；后续真实岗位审批应直接消费 [../../ipd-first-real-approval-backfill-runbook.md](../../ipd-first-real-approval-backfill-runbook.md)、[../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md)、[../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md) 和 [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md)，而不是另起一套回填路径。
- 当前已补出 Discovery replay 的直接执行清单：[08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md) 与 [08-discovery-replay-validation-package.json](08-discovery-replay-validation-package.json)；后续 `CPO / CTO / CEOChiefOfStaff` 应直接按该清单验证 seeded competitor carry-forward guard，而不是回到“先清空 Discovery evidence 再重跑”的旧做法。
- 当前已补出 module routing mode 的事后回填：[14-module-routing-mode-post-facto-backfill.md](14-module-routing-mode-post-facto-backfill.md) 与 [14-module-routing-mode-post-facto-backfill-package.json](14-module-routing-mode-post-facto-backfill-package.json)；该增量登记 `task-intake` 已支持 `deterministic / cpo / auto` 三种相关模块路由模式，并明确 CPO hook 只作为产品语义判断入口，仍需 module catalog / alias 校验与 BusinessStrategy 升级护栏。

## Evidence Surface

- [05-retrospective-memo.md](05-retrospective-memo.md)
- [05-retrospective-package.json](05-retrospective-package.json)
- [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)
- [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)
- [../../ipd-product-acceptance-contract-cpo-review.md](../../ipd-product-acceptance-contract-cpo-review.md)
- [../../ipd-runtime-evidence-contract-cto-review.md](../../ipd-runtime-evidence-contract-cto-review.md)
- [../../ipd-first-real-approval-backfill-runbook.md](../../ipd-first-real-approval-backfill-runbook.md)
- [../../ipd-first-real-approval-merge-candidate-matrix.md](../../ipd-first-real-approval-merge-candidate-matrix.md)
- [../../ipd-first-real-approval-through-pass-checklist.md](../../ipd-first-real-approval-through-pass-checklist.md)
- [../../ipd-first-real-approval-backfill-001.md](../../ipd-first-real-approval-backfill-001.md)
- [07-approval-backfill-rehearsal.md](07-approval-backfill-rehearsal.md)
- [07-approval-backfill-rehearsal-package.json](07-approval-backfill-rehearsal-package.json)
- [08-discovery-replay-validation-checklist.md](08-discovery-replay-validation-checklist.md)
- [08-discovery-replay-validation-package.json](08-discovery-replay-validation-package.json)
- [14-module-routing-mode-post-facto-backfill.md](14-module-routing-mode-post-facto-backfill.md)
- [14-module-routing-mode-post-facto-backfill-package.json](14-module-routing-mode-post-facto-backfill-package.json)
