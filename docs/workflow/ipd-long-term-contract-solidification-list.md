# IPD 长期 Contract 固化清单

版本：V0.1
日期：2026-06-14
状态：CPO / CTO 联审草案（基于 `IPD-20260611-PLATFORM-001` proving-ground replay）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-long-term-contract-solidification-list.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 待 CPO / CTO 固化后再决定是否发布到 support copy
- lastSyncedAt: 2026-06-14

## 1. 文档定位

本文不是再解释一遍 IPD 流程，而是把已经在当前 proving-ground 中跑通的东西，反整理成一份可供 `ChiefProductOfficer` 与 `ChiefTechnologyOfficer` 联审的长期 contract 固化清单。

当前判断边界保持不变：

1. 这份清单服务于赛博公司当前研发阶段和本地 Copilot-host 正式接管阶段。
2. 它不等于 TriMC 正式宿主 contract，也不等于生产级自动化平台 contract。
3. 它的依据是 `IPD-20260611-PLATFORM-001` 已完成的 `ceo-demand -> delivery` proving-ground replay，以及 `IPD-20260612-WORKFLOW-002` 仍在推进中的流程优化线。

## 2. 已核查输入

本清单当前直接建立在以下输入之上：

1. `TriCompany IPD` 主真源：[integrated-product-development-flow.md](integrated-product-development-flow.md)
2. proving-ground case 终态：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/case.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260611-PLATFORM-001/case.json)
3. proving-ground 全链路 outputs：`01-discovery.json -> 10-delivery.json`
4. proving-ground 后段 evidence：`runtime/cognition/proving-ground/IPD-20260611-PLATFORM-001/`
5. 流程优化线 machine outputs 当前已落 backlog / sprint-planning：[TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260612-WORKFLOW-002/outputs/01-backlog.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260612-WORKFLOW-002/outputs/01-backlog.json) 与 [TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260612-WORKFLOW-002/outputs/02-sprint-planning.json](../../../TriMetaverse/TriCompany-copilot-host-assets/knowledge/employees/ceo-chief-of-staff/workbench/ipd/cases/IPD-20260612-WORKFLOW-002/outputs/02-sprint-planning.json)
6. 流程优化线 source-side 闭环当前已补齐到 validation-handoff：[agile-improvement/IPD-20260612-WORKFLOW-002/03-sprint-execution-package.json](agile-improvement/IPD-20260612-WORKFLOW-002/03-sprint-execution-package.json)、[agile-improvement/IPD-20260612-WORKFLOW-002/04-sprint-review-package.json](agile-improvement/IPD-20260612-WORKFLOW-002/04-sprint-review-package.json)、[agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-package.json](agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-package.json)、[agile-improvement/IPD-20260612-WORKFLOW-002/06-validation-handoff-package.json](agile-improvement/IPD-20260612-WORKFLOW-002/06-validation-handoff-package.json)
7. 联审回填的准真实演练样本当前已形成：[agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md) 与 [agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal-package.json](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal-package.json)；它们只验证 merge / freeze 双分流路径，不构成真实岗位审批结果。
8. 第一次真实审批回填的 operator 执行稿当前已形成：[ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
9. 第一次真实审批回填的逐项 merge 预案当前已形成：[ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)

## 3. 决策

当前决策：`APPROVE with scoped freeze`

含义如下：

1. 已经在 proving-ground 中形成稳定语义、且不依赖当前单次样本巧合的内容，可以进入长期 contract 候选。
2. 仍明显依赖当前 local-only proving-ground、模拟签名、样例分数或单次 replay 的内容，先 `FREEZE` 在 proving-ground 层，不直接写成长期 contract。
3. 触碰正式宿主、生产级部署、完整岗位 adapter 或完整授权矩阵的内容，当前不在本清单内升级裁定。

## 4. 可直接进入长期 Contract 候选的项目

### 4.1 入口与治理

以下内容已经可以视为长期 contract 候选：

1. `task-intake` 必须先补齐 `clarification sheet` 的七个关键槽位，再允许进入 `Discovery`。
2. `freeze / unfreeze` 与 `reject / blocked` 必须保持语义分离，不能把条件性暂停写成拒签驳回。
3. `IPD case` 继续使用 `IPD-YYYYMMDD-文字简称-序号` 命名，不再回退到纯序号。
4. `IPD 自身优化` 固定采用 `WORKFLOW process-improvement + PLATFORM project-delivery proving-ground` 的双线闭环。

### 4.2 签核与放行

以下内容已经具备固化条件：

1. intake 与 stage output 都走 `packageHash + signerAddress + publicKey + signature` 的 web3-simulated 签核包。
2. `autopilot` 自动签不等于跳过签名，而是走 deterministic simulated wallet。
3. 阶段 release 必须显式落 `release.version / issuedAt / issuedByRole`，不能只有口头通过。
4. `CEOChiefOfStaff` 仍作为最终签发角色，负责版本签发与收口回填。

### 4.3 Discovery 与 Intelligence 输入 Contract

以下内容已经在 replay 中反复对齐，建议直接固化：

1. `Discovery` 至少交付：`reference-source-catalog.json`、`DiscoveryReferenceFunctionalBrief`、`DiscoveryCompetitorLandscape`、`DiscoveryCommonCapabilityMatrix`、`DiscoveryHighlightOpportunityMemo`。
2. `Intelligence` 必须消费 `DiscoveryReferenceFunctionalBrief`，不能跳过前一阶段直接写 PRD。
3. `Intelligence` 至少交付：`IntelligenceCapabilityExtractionMatrix`、`IntelligenceOpenSourceLandscape`、`IntelligenceCodegraphAnalysis`、`IntelligenceArchitectureOptionMemo`。
4. `Intelligence` 必须把测试、安全、并发 / 稳定性风险和运行前置条件前传给 `Designing`。

### 4.4 Designing 到 Delivery 的阶段 Contract

以下内容已经在本轮 replay 中具备最小闭环，建议进入长期 contract 候选：

1. `Designing` 必须前置架构方案、接口契约、测试基线、安全设计和 phase handoff，不得推迟到 `Coding` 之后。
2. `Coding` 必须同时保留源码改动、测试资产、配置 / 迁移改动和工程 evidence，禁止只有 narrative summary。
3. `Verify-Integration` 必须绑定聚焦验证或集成测试 evidence，不得只凭“自测通过”口头放行。
4. `Redteam` 必须显式检查安全假设、宿主边界、假完成门禁和回退锚点。
5. `QA` 的语义固定为统一质量评分 + candidate delivery manifest / report + release readiness 判断，不再退化成“测试跑过”。
6. `Deployment` 与 `Assurance` 分离：前者负责部署策略与 rollout，后者负责运行观察、恢复验证、告警 / 性能 / 成本复核与残余风险。
7. `Delivery` 必须形成 final delivery manifest / report，并完成最终 release issuance。

### 4.5 假完成门禁

以下约束建议直接写成长期底线：

1. 任一阶段至少要有一个非纯生成物 evidence path。
2. `Coding` 及后续阶段必须具备真实工程或真实验证 evidence，不允许只用 docs / workbench / autopilot 生成物假完成。
3. proving-ground 未通过时，必须回退到缺陷来源阶段，而不是把当前失败包装成“已优化完成”。

## 5. 需要 CPO 固化的产品 / 验收 Contract

当前已拆出专门的 `ChiefProductOfficer` 审批稿，见 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)。总清单只保留汇总判断；具体审批标记、冻结项和修订意见优先回填到该文档。

以下项目需要 `ChiefProductOfficer` 进一步定版：

1. `QA scorecard` 的正式放行阈值。
当前 replay 已证明 `QA scorecard + candidate delivery report` 的语义成立，但“多少分可放行、哪些维度一票否决”还未定版。
2. `Delivery` 阶段的产品完成定义。
当前已有 final delivery manifest / report，但仍需 CPO 明确“对内 proving-ground 完成”和“对外可交付完成”的边界。
3. `Discovery / Intelligence` 输出的最小验收标准。
当前已有文档集合与 functional brief / capability extraction matrix，但仍需 CPO 判断哪些字段是必须项，哪些可降级为建议项。
4. `candidate delivery` 与 `final delivery` 的切换条件。
当前 replay 已做出两层对象，但它们之间的产品放行门槛还需要书面化。

## 6. 需要 CTO 固化的 runtime / evidence Contract

当前已拆出专门的 `ChiefTechnologyOfficer` 审批稿，见 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)。总清单只保留汇总判断；具体 schema、evidence policy、签核策略和 proving-ground 冻结项优先回填到该文档。

以下项目需要 `ChiefTechnologyOfficer` 进一步定版：

1. `DesignReviewScorecard`、`QaScorecard`、`AssuranceScorecard` 的 schema 是否作为稳定 runtime contract 固化。
2. `Designing / QA / Assurance` 的 `templateFields`、`standardFlow`、`handoffChecklist` 是否直接进入稳定 schema 族。
3. `Verify-Integration`、`Redteam`、`QA`、`Deployment`、`Assurance` 的最小 evidence policy。
4. `release issuance` 与 `stage output schema` 是否拆成独立 schema family，而不是继续内嵌在当前 runtime draft structure 中。
5. `manual-ceo-signoff`、`auto_approve_roles`、`simulated wallet` 的组合规则，哪些留在 proving-ground，哪些进入常态 runtime。

## 7. 当前应继续冻结在 proving-ground 层的项目

以下项目暂不建议直接固化为长期 contract：

1. 当前 replay 中各 scorecard 的具体示例分值。
这些分值证明流程可走通，但不证明阈值本身已经合理。
2. `local-only` 的 deployment strategy 与 rollout window 描述。
这说明当前 proving-ground 可回放，不等于未来 live case 也应使用同一部署策略。
3. 当前 deterministic simulated wallet 的默认 seed 规则。
可以保留“自动签仍走签名协议”的原则，但 seed 细节不应直接写成长期对外 contract。
4. 当前 proving-ground evidence 文件名与目录布局。
目录布局可作为参考，但不应过早冻结为不可变 API。

## 8. 建议固化顺序

建议按以下顺序推进：

1. `CPO` 先定 `Discovery / Intelligence / QA / Delivery` 的产品与验收 contract。
2. `CTO` 再定 `Designing / Verify-Integration / Redteam / Deployment / Assurance` 的 runtime 与 evidence contract。
3. `CEOChiefOfStaff` 把两边结论回灌到 `IPD-20260612-WORKFLOW-002` 的后续 sprint review / retrospective / validation-handoff，当前 source-side 对应落点已固定在 [agile-improvement/IPD-20260612-WORKFLOW-002/04-sprint-review-memo.md](agile-improvement/IPD-20260612-WORKFLOW-002/04-sprint-review-memo.md)、[agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-memo.md](agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-memo.md) 与 [agile-improvement/IPD-20260612-WORKFLOW-002/06-validation-handoff-plan.md](agile-improvement/IPD-20260612-WORKFLOW-002/06-validation-handoff-plan.md)。
4. 仅在 CPO / CTO 联审通过后，再回写 [integrated-product-development-flow.md](integrated-product-development-flow.md) 与 runtime schema。

## 9. 供联审直接勾选的清单

| 项目 | 当前建议 | 主责 | 处理动作 |
| --- | --- | --- | --- |
| clarification sheet 七槽位 | 固化 | CPO + CEOChiefOfStaff | 写入长期入口 contract |
| freeze / reject 语义分离 | 固化 | CEOChiefOfStaff + CTO | 保持 runtime 状态机分离 |
| web3-simulated 签核包结构 | 固化 | CTO | 保留为稳定字段集合 |
| autopilot 自动签仍走签名协议 | 固化 | CTO | 作为 runtime 原则保留 |
| Discovery 五件套 | 固化 | CPO | 写入最小通过条件 |
| Intelligence 四件套 + 前传条件 | 固化 | CPO + CTO | 写入阶段输入 contract |
| Designing 的测试 / 安全 / handoff 前置 | 固化 | CTO | 进入稳定 stage contract |
| QA 评分语义 | 固化 | CPO + CTO | 保留语义，另定阈值 |
| QA 具体阈值 | 冻结 | CPO | 先补正式评分门槛 |
| Deployment / Assurance 分离 | 固化 | CTO | 保持双阶段分工 |
| local-only 部署策略细节 | 冻结 | CTO | 仅保留 proving-ground 使用 |
| final delivery manifest / report | 固化 | CPO | 进入长期交付对象 |
| 当前 scorecard 示例分值 | 冻结 | CPO + CTO | 不直接写成长期阈值 |

## 10. 风险

当前主要风险只有三类：

1. 把 proving-ground 跑通误写成生产级 contract 已完成。
2. 过早冻结当前目录结构、示例分值和 local-only 部署策略，导致后续 live case 反而被当前样例绑死。
3. 只改流程文档、不回写 runtime contract，导致 source truth 与执行 truth 再次分叉。

## 11. 建议收口动作

1. `ChiefProductOfficer` 先给出“固化 / 冻结 / 待补证”三色标记版。
2. `ChiefTechnologyOfficer` 再给出 runtime schema、evidence policy 和签核策略的技术定版意见。
3. `CEOChiefOfStaff` 在 `WORKFLOW-002` 后续 review 中汇总成正式收口稿，再决定是否升级回主 IPD 真源。

## 12. 联审结果回填节奏

当前联审结果默认按以下顺序回填：

1. `CPO` 先在 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 的“审批结果回填模板”中标记 `APPROVE / FREEZE / REVISE`。
2. `CTO` 再在 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 的“审批结果回填模板”中标记 `APPROVE / FREEZE / REVISE`。
3. `CEOChiefOfStaff` 把两边的 `APPROVE` 项合并回 [integrated-product-development-flow.md](integrated-product-development-flow.md) 与必要的 runtime source。
4. `CEOChiefOfStaff` 把两边的 `FREEZE / REVISE` 项回写到当前总清单，并同步整理进下一轮 `WORKFLOW-002` sprint backlog 输入；当前 backlog seeds 的 source-side 承接面默认为 [agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-memo.md](agile-improvement/IPD-20260612-WORKFLOW-002/05-retrospective-memo.md)、[agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md](agile-improvement/IPD-20260612-WORKFLOW-002/07-approval-backfill-rehearsal.md) 与下一轮 backlog package。
5. 第一次真实审批回填的操作顺序、角色边界和最小验证动作，统一以 [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md) 为准。
6. 第一次真实审批回填的逐项 landing zone、runtime 双写判断和首个验证动作，统一以 [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md) 为准。
