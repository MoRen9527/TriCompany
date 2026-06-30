# TriCompany 公司级 IPD 基线清单

版本：V0.1
日期：2026-06-15
状态：公司级 IPD 基线治理清单

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/ipd-company-baseline-checklist.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: 当前不发布；待基线治理稳定后再决定是否同步 support copy
- lastSyncedAt: 2026-06-15

## 1. 文档定位

本文只做一件事：明确赛博公司当前阶段的 IPD 流程基线，究竟由哪些 TriCompany 文件组成，以及每类文件在“流程优化 -> 验证桩验证 -> 基线回写 -> 新实例复用”闭环里分别承担什么角色。

本文不是实例文档，不承载单次审批结论，也不替代 proving-ground output、operating record 或主链切换说明。

## 2. 基线治理原则

1. 公司级 IPD 流程真源在 `TriCompany`，不在 `TriMetaverse`。
2. 流程优化验证通过后，默认先回写基线真源，再让新实例自动继承。
3. `IPD-*` case、run、proving-ground output 和 backfill batch 只是消费面 / 验证面，不是流程真源。
4. 旧实例是否补齐差异，属于历史迁移问题，不改变“先更新基线”的默认顺序。

## 3. 基线文件分层

### 3.1 A 层：书面主真源

这些文件定义公司级 IPD 的书面规则、阶段 contract 和 merge 语义；它们是流程优化后必须优先检查的回写目标。

1. [integrated-product-development-flow.md](integrated-product-development-flow.md)
   - 角色：公司级 IPD 主流程真源
   - 负责：阶段定义、岗位参与、gate、merge hook、回写原则、主线 contract
   - 默认要求：任何已批准进入长期规则的产品 / 技术 contract，都应先判断是否需要回写这里

2. [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
   - 角色：长期 contract 联审收口清单
   - 负责：承接 proving-ground 已验证能力，等待 `CPO / CTO` 决定 `APPROVE / FREEZE / REVISE`
   - 默认要求：尚未正式升级为长期规则的事项，先在这里收口，不直接写进主流程真源

### 3.2 B 层：公司执行真源

这些文件定义公司级 IPD 的可执行基线；凡是影响 runtime contract、validator、自动推进、签核语义或 evidence policy 的优化，都必须同步检查这一层。

1. [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
   - 角色：IPD stage contract 与 automation contract 的执行真源
   - 负责：阶段模板、标准动作、签核对象、evidence policy、自动推进语义

2. [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
   - 角色：IPD 基线验证真源
   - 负责：聚焦回归、案例初始化、阶段自动化、主线验证 contract

### 3.3 C 层：联审输入面

这些文件用于把 proving-ground 上已验证的能力整理为可审批对象；它们本身不是长期基线，但决定哪些能力可以升级进基线。

1. [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
2. [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md)

默认要求：

1. 只有 `APPROVE + mergeReady = yes` 的事项，才允许进入 A 层 / B 层。
2. `FREEZE / REVISE` 项继续停留在联审清单与下一轮 workflow backlog，不直接升级基线。

### 3.4 D 层：操作与实例面

这些文件服务真实回填、through-pass 执行和单次批次记录；它们属于执行资产，不是基线真源。

1. [ipd-first-real-approval-backfill-runbook.md](ipd-first-real-approval-backfill-runbook.md)
2. [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
3. [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
4. [ipd-first-real-approval-backfill-record-template.md](ipd-first-real-approval-backfill-record-template.md)
5. [ipd-first-real-approval-backfill-001.md](ipd-first-real-approval-backfill-001.md)
6. [platform-product-mainline-cutover.md](platform-product-mainline-cutover.md)

默认要求：

1. 它们可以记录“这次怎么并、并到哪里、谁来执行”。
2. 它们不能替代 A 层 / B 层成为长期流程真源。

## 4. 每次流程优化后的固定回写顺序

1. 先在 `WORKFLOW-*` 优化线完成 source-side 修改与自测。
2. 再在 `PLATFORM-*` proving-ground case 上完成实例级验证。
3. 验证通过后，先更新 B 层执行真源，确认 runtime contract 与 validation contract 成立。
4. 再更新 A 层书面主真源，把已经批准的稳定语义写入长期流程。
5. 若本轮仍需岗位联审，则先在 C 层形成审批输入，再决定哪些项能升级进 A 层 / B 层。
6. 最后才更新 D 层操作文档、主链切换说明、operating record 和发布侧摘要。

## 4.1 当前已验证 merge 实例：Discovery / Intelligence 自动化

以下内容是本清单的第一条已验证样例，用来说明一轮流程优化在 A / B / C / D 四层分别应落到哪里。

### QA / Delivery 的 A 层现状

以下书面规则已进入主流程真源：

1. [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包`
   - 已明确 `Discovery` 五件套：`reference-source-catalog.json`、`DiscoveryReferenceFunctionalBrief`、`DiscoveryCompetitorLandscape`、`DiscoveryCommonCapabilityMatrix`、`DiscoveryHighlightOpportunityMemo`
   - 已明确没有 `DiscoveryReferenceFunctionalBrief` 不得进入 `Intelligence`

2. [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD`
   - 已明确 `Intelligence` 必须消费 `DiscoveryReferenceFunctionalBrief`
   - 已明确 `Intelligence` package 至少包含 `IntelligenceCapabilityExtractionMatrix`、`IntelligenceOpenSourceLandscape`、`IntelligenceCodegraphAnalysis`、`IntelligenceArchitectureOptionMemo`
   - 已明确正式 PRD 只能基于 `IntelligenceCapabilityExtractionMatrix` 的收口结果形成

### QA / Delivery 的 B 层现状

以下执行真源已经承接该能力：

1. [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
   - 已具备 `Discovery` 自动生成 reference source catalog、functional brief、competitor landscape、common capability matrix、highlight opportunity memo 的 stage contract
   - 已具备 `Intelligence` 自动生成 source catalog、capability extraction matrix、opensource landscape、codegraph analysis、architecture option memo 的 stage contract

2. [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
   - 已覆盖 `Discovery / Intelligence` 自动化、case 初始化和阶段推进的聚焦验证

### QA / Delivery 的 C 层现状

以下联审输入面已经能承接这轮能力的长期固化判断：

1. [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
   - 已覆盖 `Discovery` 五件套、`DiscoveryReferenceFunctionalBrief` 前置约束、`Intelligence` 四件套和 `IntelligenceCapabilityExtractionMatrix` 的产品 contract 审批项

2. [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
   - 已作为这轮能力进入长期 contract 与否的联审收口面

### QA / Delivery 的 D 层现状

以下操作资产已经把这轮能力写成实例消费方式，而不是新增真源：

1. [platform-product-mainline-cutover.md](platform-product-mainline-cutover.md)
   - 已明确 `IPD-20260610-PLATFORM-001` 只消费这套基线，不再重写 `Discovery / Intelligence` 自动化 contract

2. [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
   - 已把 `Discovery` 与 `Intelligence` 相关 contract 列为 `CPO` 首批 through-pass 候选项

3. [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
   - 已把 `CPO-Discovery-Contract` 与 `CPO-Intelligence-Contract` 的 merge hook、落点和验证动作映射清楚

### QA / Delivery 的当前结论

这轮 `Discovery / Intelligence` 自动化已经不再是“待定义能力”，而是：

1. 已在 proving-ground 上验证通过。
2. 已在 A 层 / B 层形成基线落点。
3. 已在 C 层具备长期联审入口。
4. 已在 D 层明确主链实例如何消费。

因此，后续新建 IPD 实例默认直接继承这套能力；除非是特殊旧实例，否则不再单独手工吸收同一轮优化。

## 4.2 当前半固化 merge 实例：QA / Delivery contract

以下内容作为第二条样例，用来说明“验证已形成、联审入口已具备，但尚未全部升级为长期基线”的状态应如何记录。

### A 层现状

以下书面规则已经在主流程真源中具备基础落点，但仍有一部分细节停留在待联审状态：

1. [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `4. IPD 主动交付线`
   - 已具备 `QA` 阶段的 `QA package / QA scorecard / candidate delivery manifest / candidate delivery report`
   - 已具备 `Delivery` 阶段的 `Delivery package / final delivery manifest / final delivery report`

2. [integrated-product-development-flow.md](integrated-product-development-flow.md) 的 `6. 关键门禁`
   - 已具备 `产品验收` 与 `总助收口` 的基础门禁落点
   - 但 `QA` 评分阈值、一票否决维度、`candidate delivery -> final delivery` 的精确升级门槛，当前仍不应写成已定长期规则

### B 层现状

以下执行真源已具备后段阶段骨架，但并不代表所有 `QA / Delivery` 细节都已完成长期固化：

1. [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py)
   - 已具备 `QA`、`Deployment`、`Assurance`、`Delivery` 的阶段模板与 package 草稿落点
   - 但 `QA` 分值阈值、一票否决维度、`candidate delivery -> final delivery` 的精确规则，当前不应视为已完全固化的长期执行 contract

2. [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py)
   - 当前可作为后段阶段验证 contract 的承接面
   - 但若未来正式固化 `QA / Delivery` 精细规则，仍应补对应聚焦验证，而不是只停留在文档层说明

### C 层现状

这轮能力当前主要停留在联审输入面，是“具备升级入口，但尚未全部升级完成”的典型例子：

1. [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md)
   - 已明确 `QA = 统一质量评分 + candidate delivery 对象 + readiness 判断`
   - 已明确 `Delivery` 必须产出 `final delivery manifest / report`
   - 已明确 `Delivery` 不等于生产级上线完成
   - 同时也明确把 `QA` 具体阈值、一票否决维度、`candidate delivery -> final delivery` 门槛保留为 `FREEZE` 候选

2. [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)
   - 应继续作为这组 contract 的长期联审收口面，直到 `APPROVE / FREEZE / REVISE` 被真实写定

### D 层现状

以下操作资产已明确这组 contract 的消费与回写方式：

1. [ipd-first-real-approval-through-pass-checklist.md](ipd-first-real-approval-through-pass-checklist.md)
   - 已把 `QA = 统一评分 + candidate delivery 对象 + readiness 判断`
   - `Delivery 必须产出 final manifest / report`
   - `Delivery 不等于生产级上线完成`
   列为首批 through-pass 候选项

2. [ipd-first-real-approval-merge-candidate-matrix.md](ipd-first-real-approval-merge-candidate-matrix.md)
   - 已把上述 `APPROVE` 候选与 `QA` 阈值 / 一票否决 / delivery 升级门槛的 `FREEZE` 候选分开映射

3. [platform-product-mainline-cutover.md](platform-product-mainline-cutover.md)
   - 已明确主链后续验证要围绕真实代码、调用结果、前端 smoke 和交付边界，而不是继续围绕审批稿本身打转

### 当前结论

这轮 `QA / Delivery` contract 当前应按“半固化”理解：

1. 基础语义和主要对象已经有 A 层 / D 层落点。
2. 执行真源已经有 B 层承接骨架。
3. 但精细阈值、精确升级门槛和一票否决维度仍主要停留在 C 层待联审状态。
4. 因此，新实例可以继承已经稳定的 `QA / Delivery` 基础语义，但不应假定所有评分细则和 delivery 升级门槛都已成为长期默认规则。

## 5. 新实例默认继承规则

1. 新创建的 IPD 实例默认继承 A 层 + B 层的最新基线。
2. 不需要为新实例重复手工合入已经进入基线的流程优化。
3. 只有旧实例、冻结后重开实例或历史回放实例，才需要判断是否补齐差异。

## 6. 最小检查清单

当一次流程优化声称“已经进入公司级 IPD 基线”时，至少检查：

1. [integrated-product-development-flow.md](integrated-product-development-flow.md) 是否已更新，或明确说明本轮只改执行真源不改书面语义。
2. [../../runtime/cognition/ipd_case_engine.py](../../runtime/cognition/ipd_case_engine.py) 是否已更新，或明确说明本轮只改书面语义不改执行 contract。
3. [../../runtime/cognition/chief_of_staff_ipd_case_validation.py](../../runtime/cognition/chief_of_staff_ipd_case_validation.py) 是否已补齐对应验证。
4. 若仍有待审批事项，[ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 是否已记录。
5. 若需要让发布侧同步，`TriMetaverse` 的摘要 / 镜像文档是否已追平。

## 7. Guardrails

1. 不得把 proving-ground output 直接写成公司级流程真源。
2. 不得只改实例说明文档，而不改 A 层 / B 层基线文件。
3. 不得把联审输入稿误写成已生效长期规则。
4. 不得把当前阶段口径外推为 `TriMC` 正式宿主或生产级自动化平台 contract。
