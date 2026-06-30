# IPD-20260612-WORKFLOW-002 Retrospective Memo

## What Worked

### 1. proving-ground replay 已经能反整理成稳定联审链

- 这轮不再只是停留在 replay 成功，而是把 replay 中验证过的 contract 候选拆成总清单、产品审批稿和技术审批稿。
- 这说明流程优化线已经能从“跑通一次”前进到“为长期规则固化做准备”。

### 2. 主流程真源与审批稿之间的映射关系已经被显式化

- 主流程真源现在知道每类审批项该回写到哪里。
- 审批稿也直接带上 merge hook，后续审批不再需要二次人工翻译。

### 3. 文档真源与校验动作保持了同步

- 这轮没有先改很多文档再留着后面补检查，而是把关键文档一起做了诊断校验。
- 这种“补真源同时做聚焦校验”的节奏，适合作为后续联审回填的默认工作方式。

## What Did Not Work

### 1. 真实审批与准备链仍是两个不同阶段

- 当前已经把审批稿写好，不等于审批已经发生。
- 如果不反复强调这一点，就容易把“ready for review”误写成“review approved”。

### 2. runtime 回写仍然依赖真实岗位决定

- 目前已经知道 runtime 该回写到哪里。
- 但没有真实 `CTO` 决策前，依然不能把候选规则提前固化到 source runtime。

### 3. `FREEZE / REVISE` 项的回流还没有跑一次实战

- 规则已经写出来了。
- 但下一轮 backlog 如何接住冻结项，还需要一次真实审批后的演练或正式回填来证明。

## Next Backlog Seeds

### 1. 真实跑一轮审批回填

- 让 `ChiefProductOfficer` 与 `ChiefTechnologyOfficer` 在各自审批稿上真实填写至少一轮结论。
- 用真实结论验证 `mergeReady -> 主流程回写` 与 `FREEZE / REVISE -> backlog seeds` 两条分流是否顺畅。

### 2. 把通过项双写回主流程与 runtime

- 对需要双写的技术 contract，验证“文档真源 + runtime 真源”是否能在同轮或下一轮收口。
- 避免再次出现流程文档已经升级、执行真源仍停在旧规则的分叉。

### 3. 固定冻结项回流模板

- 在下一轮 backlog 中显式加入来自 `CPO / CTO` 审批稿的冻结项种子。
- 把“审批冻结项 -> workflow backlog”这条路固化成固定模板，而不是临时发挥。

## Retrospective Guardrails

- 当前结论成立于本地 Copilot-host 正式接管阶段，不等于 TriMC 正式宿主已经接管。
- 当前结论属于流程优化线，不等于真实商业交付线或生产级 contract 已验证完成。
- validation-handoff 必须把“可直接 merge 的规则”和“必须继续冻结的规则”拆开，不能混写。

## Evidence Surface

- [04-sprint-review-memo.md](04-sprint-review-memo.md)
- [04-sprint-review-package.json](04-sprint-review-package.json)
- [../../integrated-product-development-flow.md](../../integrated-product-development-flow.md)
- [../../ipd-long-term-contract-solidification-list.md](../../ipd-long-term-contract-solidification-list.md)
- [../../ipd-product-acceptance-contract-cpo-review.md](../../ipd-product-acceptance-contract-cpo-review.md)
- [../../ipd-runtime-evidence-contract-cto-review.md](../../ipd-runtime-evidence-contract-cto-review.md)
