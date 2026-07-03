# 集成产品开发流程（IPD 流程）

版本：V0.6
日期：2026-06-29
状态：当前 Copilot-host live 阶段流程设计（补充 training / signing / stage contract 细化，挂接长期 contract 固化清单与联审 merge hook，并对齐 20260611 / 20260610 / WORKFLOW-002 的验证边界）

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/integrated-product-development-flow.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/integrated-product-development-flow.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-29

## 1. 文档定位

本文定义 TriCompany 当前阶段的集成产品开发流程（IPD 流程）。

当前项目真源改按以下三层关系理解：

1. `TriCompany` 负责公司侧流程、员工参与、资料组织、门禁完善与书面核签——即 IPD 的**公司协同层**。
2. `TriDev` 负责开发型项目的项目级十阶段 phase engine——即 IPD 的**流程执行层**。
3. `Tride` 负责本地编码智能体、CLI runtime 与 agentic orchestration 底座——即 IPD 的**本地编码层**（当 Tride 可用时接入；当前仍待初始化，不可写成已生产就绪）。
4. `IPD` 是同时包含公司协同层、流程执行层与本地编码层的统一交付体系，不是与项目十阶段并行的第二套开发流程。`process-improvement`（IPD 自身流程优化线）可能针对这三层中任一位置进行优化；`project-delivery`（项目交付线）由三层共同协作完成交付。

当前设计只代表赛博公司研发阶段和本地 Copilot-host 正式接管阶段，不代表 TriMC 正式宿主、生产级自动运营看板或完整授权矩阵已经完成。

当前公司级 IPD 基线由哪些书面真源、执行真源、联审输入面和操作资产组成，统一见 [ipd-company-baseline-checklist.md](ipd-company-baseline-checklist.md)。后续任何流程优化若要宣称“进入公司级 IPD 基线”，默认按该清单执行回写与校验。

## 2. 流程总名与两条线

当前总名采用：

- `TriCompany IPD 双线闭环`

两条工作线分别为：

- `IPD 市场雷达线`：由 CMO 主责，持续发现公司内外部需求、市场信号、竞品变化、热点、用户痛点和风险机会；该线只形成机会候选和市场真实需求判断，不直接启动开发。
- `IPD 主动交付线`：由 CEO / CEOChiefOfStaff 正式下发需求或任务后启动；公司员工按 CMO、COO、CFO、CPO、CTO、开发执行、验收、运营、财务、总助收口的顺序参与，而流程主线默认挂接到 `TriDev` 的项目级十阶段。

两条线的衔接规则：

`IPD 市场雷达线 -> CEO / CEOChiefOfStaff 决策 -> 正式需求 / 任务 -> IPD 主动交付线`

### 2.1 IPD 自身优化与固定验证桩闭环

当前对 IPD 自身的优化，不应直接混在某一条 `project-delivery` case 里完成，而应固定采用双线反复闭环：

1. 流程优化线：使用独立 `process-improvement + WORKFLOW` case，以 agile-improvement 方式优化 intake、dispatch、rollback、各阶段提交 / 签核、自测与门禁语义。
2. 真实验证线：使用固定 `project-delivery` case 回放已优化能力。当前口径必须区分两条 `PLATFORM` case：`IPD-20260611-PLATFORM-001` 已完成 `ceo-demand -> delivery` 全链路 proving-ground replay，作为已验证能力与长期 contract 候选的证据基线；后续 Gate A / Gate B / Gate C 的继续优化与产品主线消费，转到 full-scope case `IPD-20260610-PLATFORM-001`。

`IPD-20260610-PLATFORM-001` 的最终目标是逐步消费已并入的 IPD 基线并验证完整模型 API 平台主线，而不是继续把 `IPD-20260611-PLATFORM-001` 当成未完成的 Gate A/B/C 目标。当前建议按 capability gate 推进：

- Gate A：`ceo-demand -> task-dispatch -> discovery -> intelligence -> package/signoff`
- Gate B：`designing -> coding -> verify-integration`
- Gate C：`redteam -> qa -> deployment -> assurance -> delivery`

每轮规则固定为：

`process-improvement workflow sprint（当前为 IPD-20260612-WORKFLOW-002） -> source-side 自测 -> 切片验证 -> IPD-20260610-PLATFORM-001 live replay / 产品主线消费 -> 继续 / 冻结 / 回退`

若 `IPD-20260610-PLATFORM-001` 的 replay 或产品主线消费未通过，不直接在原 case 里口头解释为“流程已优化完成”，而是按缺陷来源回退到 `ceo-demand`、`task-dispatch`、`discovery` 或必要的后续阶段，再把问题回灌到 `IPD-20260612-WORKFLOW-002` 或下一条 workflow sprint case。

基于 `IPD-20260611-PLATFORM-001` 已完成的 `ceo-demand -> delivery` proving-ground replay，当前已单独整理出一份供 `CPO / CTO` 联审的长期 contract 固化清单：[ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md)。主流程文档继续负责定义 canonical 流程；是否把 replay 中验证过的字段、scorecard schema、evidence policy 和放行规则升级为长期 contract，以该清单的联审结论为准。

### 2.2 联审 merge hook 与回写落点

为避免 `CPO / CTO` 联审后再次出现“审批结论存在，但主流程真源不知道该改哪里”的分叉，当前主流程文档预埋以下 merge hook：

1. `CPO-Discovery-Contract`：对应 [ipd-product-acceptance-contract-cpo-review.md](ipd-product-acceptance-contract-cpo-review.md) 中 `Discovery` 最小输入 contract 的 `APPROVE` 项，默认回写到 `4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包`。
2. `CPO-Intelligence-Contract`：对应 `Intelligence` 最小收口 contract 的 `APPROVE` 项，默认回写到 `4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD`。
3. `CPO-QA-Delivery-Contract`：对应 `QA` 验收语义与 `Delivery` 完成定义的 `APPROVE` 项，默认回写到 `4. 主动交付线` 阶段表、`6. 关键门禁` 和后续交付边界说明。
4. `CTO-Stage-Template-Contract`：对应 [ipd-runtime-evidence-contract-cto-review.md](ipd-runtime-evidence-contract-cto-review.md) 中 `templateFields / standardFlow / handoffChecklist` 的 `APPROVE` 项，默认回写到 `4. 主动交付线` 阶段表和 `TriCompany/runtime/cognition/ipd_case_engine.py`。
5. `CTO-Evidence-Policy-Contract`：对应后段 `evidence policy` 的 `APPROVE` 项，默认回写到 `4. 主动交付线` 各阶段说明、`6. 关键门禁` 与 runtime validator。
6. `CTO-Signing-Release-Contract`：对应 `packageHash / signatureChain / release issuance / manual-ceo-signoff` 的 `APPROVE` 项，默认回写到 `4.0.2 Web3 签核与 autopilot` 与 runtime source。

当前回写规则固定如下：

1. 只有审批稿中被明确标记为 `APPROVE`，且签发区 `mergeReady = yes` 的项目，才允许合并回主流程真源。
2. 被标记为 `FREEZE` 或 `REVISE` 的项目，不回写主流程真源，而是继续回写到 [ipd-long-term-contract-solidification-list.md](ipd-long-term-contract-solidification-list.md) 和 `WORKFLOW-002` backlog。
3. 任何需要同时改文档与 runtime 的 `APPROVE` 项，必须同轮或下一轮完成双写，避免 source truth 与 execution truth 再次分叉。
4. 当前 merge hook 只服务于赛博公司研发阶段与本地 Copilot-host 正式接管边界，不自动外推为 `TriMC` 正式宿主或生产级发布 contract。

## 3. IPD 市场雷达线

市场雷达线是被动机会发现机制，不等于正式立项。

| 阶段 | 主责 | 参与 | 输入 | 输出 |
| --- | --- | --- | --- | --- |
| 1. 日常市场扫描 | CMO | CEOChiefOfStaff、CPO、COO、CFO | 竞品、行业新闻、热点、用户反馈、公司内部需求、销售或运营线索 | 市场雷达日报 / 周报 |
| 2. 机会归类 | CMO | CPO、COO、CFO | 市场雷达材料 | 用户痛点、产品机会、运营机会、财务风险、待验证假设 |
| 3. 初筛建议 | CMO | CEOChiefOfStaff | 高价值机会候选 | 机会建议、证据摘要、建议是否进入决策 |
| 4. 决策分流 | CEO / CEOChiefOfStaff | CMO、CPO、COO、CFO、CTO | 机会建议 | 丢弃、继续观察、补充调研、进入正式任务 |
| 5. 主动线触发 | CEO / CEOChiefOfStaff | CMO、CPO、COO、CFO、CTO | 正式任务决定 | IPD 主动交付线启动 |

市场雷达线的最小证据要求：

- 来源、时间、样本范围和可信度。
- 事实、判断、假设和待验证问题分开写。
- 不能把未经验证的搜索材料包装成市场结论。
- 不能绕过 CEO / CEOChiefOfStaff 决策直接要求 TriDev 开发。

## 4. IPD 主动交付线

主动交付线用于把正式需求或任务推进到产品交付、运营和财务收口。

对开发型产品，当前 canonical 口径已进一步落到 source-side runtime：`TriDev` 直接承接项目级十阶段主线，`TriCompany IPD case` 负责把员工参与、资料与核签要求一比一挂到这条主线上。

当前 source-side runtime 已开始按 discovery 到 delivery 的 ten-phase stage line 生成 work item、phase package draft、书面签核和自动推进；阶段 contract 已显式带出 `businessOwner / actingOwner / moduleExecutor / gateOwner`，其中 `TriDev` 作为 Discovery 到 Delivery 的统一执行引擎，当前默认由 CPO / CTO 担任业务或代理 owner。`chief_of_staff_ipd_case autopilot` 已可自动提交阶段产物、自动完成顺序签核，并在可用时桥接 TriDev run 的 phase result / gate / delivery bundle；默认全自动签核，也支持在 CEO 签核点切到人工暂停模式。当前仍未完成的是 PRD 分叉并行、多分支 delivery 聚合、独立 phase package schema 族和完整岗位 adapter。

当前 IPD 入口新增 `clarification sheet`。当 CEO / 总助以 freeform 任务进入 `task-intake` 时，总助必须先补齐关键槽位，才能正式把事项分派到 Discovery：

- `competitorReference`：如果原始需求没有竞品 / 对标对象，总助必须补问一轮。
- `targetUserScenario`：首轮目标用户与使用场景。
- `deliveryWindow`：期望工期 / 节奏。
- `budgetGuardrail`：预算护栏 / 成本窗口。
- `successMetric`：首轮成功信号。
- `mustHaveScope`：必须交付的最小范围。
- `explicitOutOfScope`：明确不做项。

当前 runtime 已把这些槽位写入 intake brief；未补齐时，case 会停在 `paused-intake-clarification`，不允许进入 Discovery。

### 4.0.1 IPD case 命名治理

- 自 2026-06-11 起，TriCompany 公司级治理口径统一要求 `IPD case` 使用 **`IPD-YYYYMMDD-文字简称-序号`**；不再新建 `IPD-001` 这类纯序号 case。
- `文字简称` 用于表达当前事项的最小可读主题，优先使用全大写 ASCII 短词；`序号` 固定为三位数，在同日同简称下从 `001` 递增，例如：`IPD-20260611-PLATFORM-001`、`IPD-20260611-WORKFLOW-001`。
- CLI 默认自动生成也遵循同一规则，会根据任务内容推导最小简称，避免 runtime、会议纪要、reference 目录和 handoff 文档各自发明不同命名。
- Discovery / Intelligence reference 目录、owner-action package、阶段 work item、会议纪要和后续回填文档，都必须复用同一条 date-first case id，不得混用旧式编号。
- 已存在的历史 case 可以保留原编号；但新建 case、重放 case 或重新进入 live 流程时，应优先迁到该规则。

当关键槽位全部补齐后，`CEOChiefOfStaff` 还需要做一轮项目可行性判断；如果认为当前资源、目标、阶段边界或范围条件暂时不成立，可以先把 case 冻结为 `paused-frozen`。当条件补齐后，应通过 `unfreeze` 恢复，而不是把这类条件性问题直接写成拒签驳回。

### 4.0.2 Web3 签核与 autopilot

- 当前 intake 和 stage signoff 都已切到 `packageHash + signerAddress + publicKey + signature` 的 web3-simulated 签核包。
- 人工签核时，可以通过 `--signing-key` 或 `--mnemonic` 显式提供凭据。
- autopilot 默认仍可自动推进，因为当没有显式凭据输入时，runtime 会按岗位 default seed 生成 deterministic simulated wallet 进行自动签名；这表示“自动签核仍走签名协议”，不表示跳过签名。
- 如果需要保留人工 CEO 签核点，可通过 `manual-ceo-signoff` 或限制 `auto_approve_roles` 让 autopilot 在对应签核点暂停。

| 阶段 | businessOwner | actingOwner | moduleExecutor | gateOwner | 参与 | 关键职责 | 输出 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Discovery | CPO | CPO | TriDev | CPO | CEOChiefOfStaff、CEO、CMO、CTO | 沉淀任务意图、目标边界、Discovery 真源草稿和 raw evidence pack；按总助拆解的研发任务搜索产品与官方手册并落到 `TriMetaverse/reference/discovery/<case-id>/`；当前默认由 CPO 搜索竞品、功能、官方手册并收 `DiscoveryReferenceFunctionalBrief`，由 CMO 验证需求是否合理、是否是真需求（当前可先占位）；如果 CMO 判断这不是市场真实需求，可在 Discovery 期间直接冻结 case；完成任务模块命中判断；对命中的既有正式模块准备标配审计与 init；如涉及新正式模块，同步生成模块标配单项发布草案 | Discovery package、reference source catalog、DiscoveryReferenceFunctionalBrief、ModuleTargetingReport、ModuleReadinessInitReport（如涉及既有模块）、NewModuleBaselineRelease（如涉及新模块） |
| 2. Intelligence | CPO | CPO | TriDev | CPO | CEOChiefOfStaff、CMO、COO、CFO、CTO | 消费 `DiscoveryReferenceFunctionalBrief`；搜索相关开源代码并落到 `TriMetaverse/reference/intelligence/<case-id>/`；当前默认由 CTO 搜索开源代码、建立本地 CodeGraph、做 capability extraction，辅助 CPO 收正式 PRD；同步抽取可复用的测试思路、质量门、安全约束和运行前置条件，作为 Designing 输入；COO / CFO 的运营约束与预算护栏当前先占位，后续再补自动岗位实现；CPO / CTO / COO / CFO 在自己负责窗口都可以基于专业判断冻结 case；再把市场、运营、财务输入收口成正式 PRD / 项目计划 / 验收标准 | Intelligence package、reference source catalog、IntelligenceCapabilityExtractionMatrix、PRD、项目计划 |
| 3. Designing | CTO | CTO | TriDev | CTO | CPO、CEOChiefOfStaff | 产出产品技术选型、系统架构、工程门禁、任务拆解、phase handoff、MVP 与 full-PRD phased plan；同时形成测试策略 / 测试用例基线、回归范围、安全与 redteam 前置设计，确保 Verify-Integration、QA 和 Redteam 有前置 contract 可执行 | Design package、架构方案、测试设计基线、安全设计说明、实施计划 |
| 4. Coding | CTO | CTO | TriDev | CTO | CPO、CEOChiefOfStaff | 基于 Designing 阶段的架构、计划和测试基线执行开发实现；同步沉淀代码、测试资产、配置 / 迁移改动、失败 / 回滚记录和工程证据；如当前编码由 Copilot 等宿主完成，也应保留后续切到 `Tride` 本地编码智能体底座的适配空间 | Coding package、源码改动、测试资产、配置 / 迁移改动、开发产物 |
| 5. Verify-Integration | CTO | CTO | TriDev | CTO | CPO、CEOChiefOfStaff | 按 Designing 阶段定义的测试基线、phase handoff 和集成边界执行系统级验证、集成测试、回归测试和缺陷收口 | Verify package、integration / regression evidence |
| 6. Redteam | CTO | CTO | TriDev | CTO | CEOChiefOfStaff | 执行对抗审查、安全验证、残余风险分级和整改要求；优先验证 Designing 阶段预置的安全假设、边界防护和 threat model 是否成立 | Redteam package、安全整改清单、残余风险说明 |
| 7. QA | CTO | CTO | TriDev | CTO | CPO、CEOChiefOfStaff | 给出统一质量评分、release readiness 结论，并形成 candidate delivery manifest / report；评分至少覆盖设计缺陷、代码质量、架构合理性、测试覆盖率、回归情况、残余 bug 与修复成本、安全评估、并发性、稳定性和健壮性 | QA package、QA scorecard、candidate delivery manifest、candidate delivery report |
| 8. Deployment | CTO | CTO（未来可切 deployee-xxx） | TriDev | CTO | COO、CFO、CEOChiefOfStaff | 先选择并执行最合适的 AI 自动化部署方案（如本地、单机、容器、k8s、渐进发布等），再沉淀部署证据、发布说明、上线窗口和 rollout plan | Deployment package、deployment strategy record、deployment evidence、rollout plan |
| 9. Assurance | CTO | CTO（未来可切 tester-xxx / deployer-xxx） | TriDev | CTO | COO、CFO、CEOChiefOfStaff | 沉淀运行观察、回滚演练、恢复验证、告警 / 性能 / 成本复核、残余风险追踪和 assurance evidence，形成保驾窗口内的稳定性结论 | Assurance package、runtime observation report、recovery validation report、assurance evidence |
| 10. Delivery | CPO | CPO | TriDev | CPO | CEOChiefOfStaff、CEO、COO、CFO、CTO | 形成最终交付结论、final delivery manifest / report、版本化 gate package、运营接管输入和后续动作 | Delivery package、final delivery manifest、final delivery report |

### 4.1 Discovery 标准动作：新模块单项发布

- 当 `Discovery` 判断该事项需要新增正式模块（而非落到既有模块）时，必须同步形成 `NewModuleBaselineRelease`，并作为阶段内标准产物进入门禁。
- `NewModuleBaselineRelease` 最小内容：
  1. 模块归属路由与边界结论（既有模块 / 新正式模块）。
  2. 模块标配骨架：独立 git 仓、`README.md`、`docs/` 六件套、根级 `.gitignore`、本地 CodeGraph 初始化计划。
  3. `vendor-extraction-profile`：source、version anchor、subpath 映射、patch 策略、回滚点与审计说明。
  4. owner 与签核链：CPO（归属）、CTO（技术与抽取）、CAO（治理）、总助与 CEO（放行）。
- 发布状态机固定为 `candidate -> approved -> init`：
  - `candidate`：Discovery 草案阶段，可迭代，不得写成已落地模块。
  - `approved`：完成跨岗位签核，允许进入初始化执行。
  - `init`：由 `TriDev init` 消费已签核发布包并落下模块骨架。
- `TriDev init` 属于流程层执行动作，不替代 CPO 的归属判断、CTO 的长期技术路线设计和后续 `INTELLIGENCE / DESIGNING` 的正式收口。

### 4.2 Discovery 标准动作：既有模块命中与就绪初始化

- 当 `Discovery` 判断任务应落在既有正式模块时，必须先形成 `ModuleTargetingReport`，明确主模块、次模块、依赖关系和命中理由。
- `ModuleTargetingReport` 完成后，由 `TriDev` 对命中模块执行 `ModuleReadinessInit`，状态机固定为 `identified -> audited -> init`：
  - `identified`：模块命中清单已确认。
  - `audited`：完成标配审计（git、`README.md`、`docs/` 六件套、`.gitignore`、CodeGraph）。
  - `init`：只对缺口做基线补齐，不做业务重构。
- `ModuleReadinessInit` 通过后，才允许进入后续 `INTELLIGENCE / DESIGNING / CODING` 的业务开发阶段。

### 4.3 Discovery 标准动作：产品 / 官方手册 reference 发现包

`Merge hook: CPO-Discovery-Contract`

- `Discovery` 现在固定带一条 reference 发现动作：CPO 必须根据总助拆解后的研发任务，全网搜索符合情况的产品及其官方手册，并把一手材料下载到 `TriMetaverse/reference/discovery/<case-id>/`。
- Discovery reference 发现包最少包含：
  1. `reference-source-catalog.json`：记录产品名、来源链接、是否官方、下载位置、用途说明。
  2. `discovery-reference-functional-brief.md`：统一命名为 `DiscoveryReferenceFunctionalBrief`，总结典型功能、输入输出、边界、不做项和待验证问题。
  3. `discovery-competitor-landscape.md`：统一命名为 `DiscoveryCompetitorLandscape`，登记竞品、官方入口、手册入口、核心功能和差异点。
  4. `discovery-common-capability-matrix.md`：统一命名为 `DiscoveryCommonCapabilityMatrix`，抽取共性功能、输入输出和当前阶段边界。
  5. `discovery-highlight-opportunity-memo.md`：统一命名为 `DiscoveryHighlightOpportunityMemo`，沉淀亮点功能、差异化机会和后续需要 Intelligence 深挖的点。
  6. 原始材料：官网页面、官方 README、官方 docs、API 手册、产品说明页、定价页或其他一手资料快照。
- 当前 runtime 在 Discovery 激活时会自动生成上述 markdown package 草稿；CPO 需要在自动草稿上继续补齐真实内容，而不是只保留空模板。
- `DiscoveryReferenceFunctionalBrief` 不是对同目录其他文档的简单重复拷贝，而是把 `reference-source-catalog.json`、`DiscoveryCompetitorLandscape`、`DiscoveryCommonCapabilityMatrix`、`DiscoveryHighlightOpportunityMemo` 和原始材料统一归一后的工作摘要；它的目标是为后续 Intelligence 提供一份稳定、收口、可直接消费的输入 contract。
- 如果 Discovery 只有原始链接、没有 `DiscoveryReferenceFunctionalBrief`、共性功能矩阵和亮点功能 memo，则不允许直接进入开源代码搜索或正式 PRD 收口。

### 4.4 Intelligence 标准动作：开源代码 reference、CodeGraph 与正式 PRD

`Merge hook: CPO-Intelligence-Contract`

- `Intelligence` 固定以前一阶段的 `DiscoveryReferenceFunctionalBrief` 为直接输入，不允许跳过产品 / 官方手册研究直接写 PRD。
- Intelligence 最少包含三步：
  1. 根据 `DiscoveryReferenceFunctionalBrief` 搜索相关开源代码，把代码快照或锚点记录落到 `TriMetaverse/reference/intelligence/<case-id>/`。
  2. 对主要代码参考建立本地 CodeGraph；如果复用中心 reference 锚点，也必须在 intelligence 目录记录锚点路径和索引位置。若当前宿主暂未挂载 CodeGraph，至少要先登记待建索引动作和结构化深读范围。
  3. 基于代码深入分析形成 `intelligence-capability-extraction-matrix.md`，统一命名为 `IntelligenceCapabilityExtractionMatrix`，明确纳入 / 后置 / 排除项，再据此书写正式 PRD。
  4. 同步提取测试思路、质量门、安全约束、并发 / 稳定性风险和运行前置条件，为 Designing 阶段形成测试与 security-by-design 基线。
- Intelligence markdown package 还必须包含：
  1. `intelligence-opensource-landscape.md`：统一命名为 `IntelligenceOpenSourceLandscape`，登记开源仓库、公开资料、参考价值和深读优先级。
  2. `intelligence-codegraph-analysis.md`：统一命名为 `IntelligenceCodegraphAnalysis`，记录 CodeGraph 深读重点、核心模块、调用链和与需求的对应关系。
  3. `intelligence-architecture-option-memo.md`：统一命名为 `IntelligenceArchitectureOptionMemo`，总结共性功能与亮点功能的架构选型、实现思路和首轮取舍建议。
- 当前 runtime 在 Intelligence 激活时会自动生成上述 markdown package 草稿；CTO 需要基于上一阶段资料继续补齐真实代码分析与架构判断。
- 正式 PRD 只能基于 `IntelligenceCapabilityExtractionMatrix` 提取符合我们需求的功能，不得直接照搬上游代码结构、商业假设或合规假设。

### 4.5 专业冻结权限

- `CEOChiefOfStaff`：在 intake `clarification sheet = ready-for-dispatch` 后，必须再做一轮项目可行性判断；如果认为项目当前不可行，可以直接冻结 case。
- `ChiefMarketingOfficer`：在 `Discovery` 期间，如果调研后确认这不是市场真实需求，可以直接冻结 case。
- `ChiefProductOfficer`、`ChiefTechnologyOfficer`、`ChiefOperatingOfficer`、`ChiefFinancialOfficer`：在自己负责的阶段窗口内，可以基于产品、技术、运营、财务判断冻结 case。
- 未来新增的 IPD 员工不再需要硬编码单独规则；只要进入 IPD 的 `roleAssignmentMatrix` 且 `canFreezeCase=true`，就自动具备同样的冻结权限。
- `freeze` 是条件性暂停：当前 runtime 会把 case 置为 `paused-frozen` 并阻止继续 submit / signoff / autopilot；当冻结条件满足后，需要由原冻结岗位或 `CEOChiefOfStaff` 执行 `unfreeze` 恢复。
- `reject` / `rejected` 是完全不同的语义：它表示当前提交内容不被接受或判断为不可行，case 会进入 `blocked`，需要责任岗位重提、重签或重走节点，而不是简单解冻。

## 5. TriDev 接入规则

这里不要把 TriDev 理解成表里某一个瞬时“开发执行”动作。

更准确地说，在当前 canonical 口径里：

1. `TriDev` 是开发型项目从 `Discovery` 到 `Delivery` 的十阶段流程层 / phase engine。
2. `TriCompany IPD case` 是公司侧任务、资料、门禁、核签和跨岗位协同层。
3. 赛博公司的员工在 `TriDev` 十阶段各节点参与提交资料、完善门禁、形成可签发版本号的 gate package，再由总助 / CEO 决定是否放行下一阶段。
4. 当前 source-side runtime 已按 ten-stage 提供 discovery 到 delivery 的一比一 stage line，并显式区分 `businessOwner / actingOwner / moduleExecutor / gateOwner`；PRD 分叉并行、多分支 delivery 聚合、独立 package schema 族和完整岗位 adapter 仍待继续补齐。

在当前 source-side runtime 里，TriDev 在既有模块场景可从 `Discovery` 的 `ModuleReadinessInit` 提前进入（完成命中模块标配审计与缺口 init）；在新模块场景可从 `Discovery` 的 `init` 提前进入（消费 `NewModuleBaselineRelease` 执行模块骨架初始化），并在 designing / coding 阶段持续承接 phase engine；更早的公司侧分诊与更晚的经营复盘，仍由 TriCompany 组织员工参与和书面放行。

1. CEO / CEOChiefOfStaff 已确认该事项进入 IPD 主动交付线。
2. CMO 已提供最小市场证据或 CEO 明确允许跳过补证。
3. COO 已给出上线节奏、试点路径或运营约束。
4. CFO 已给出预算护栏、成本约束或停止条件。
5. CPO 已给出 PRD、MVP 范围、验收标准和项目计划。
6. CTO 已给出技术路线、开发任务拆解和工程门禁。
7. 若涉及新正式模块：`NewModuleBaselineRelease` 已达到 `approved`，且 `TriDev init` 已完成首轮骨架初始化。
8. 若涉及既有正式模块：`ModuleTargetingReport` 已确认，且 `ModuleReadinessInit` 已完成。

补充边界：

1. `TriDev` 负责开发型项目的 workflow / gate / evidence / release engine。
2. `Tride` 负责本地编码智能体、CLI runtime 与 agentic orchestration 底座；当 Coding 阶段需要更稳定的本地编码执行面时，应优先考虑由 `TriDev -> Tride` 建立适配，而不是把编码执行永远绑死在当前宿主入口。
3. `TriHost`（当前为 Copilot-host，未来目标可转 `TriMC`）负责的是赛博公司整体运行宿主与交互主控，不等于本地编码智能体底座。
4. 因此 `TriHost/TriMC` 与 `Tride` 不是替代关系，而是“公司宿主层”和“本地编码执行层”的分工关系；`TriDev` 则位于其上的流程执行层。

TriDev 接入后负责：

- 维护开发型项目的十阶段流程层、phase state、分叉与版本包签发。
- 建立开发 run。
- 沉淀从 discovery 到 delivery 的 gate / evidence / artifact / 版本包。
- 绑定 PRD、技术方案、市场证据、运营计划和预算护栏为输入证据。
- 执行阶段 gate、artifact 记录、digest 校验、failure / rollback / resume 和 release bundle。
- 将可验收产物交回 CTO / CPO。
- 将交付证据提供给 COO 做运营接管，提供给 CFO 做决算复盘。

TriDev 不负责：

- 决定是否立项。
- 替 CMO 做市场判断。
- 替 CPO 写产品范围和验收标准。
- 替 COO 负责运营复盘。
- 替 CFO 负责预算和决算。
- 替 CTO 决定长期技术路线。

## 6. 关键门禁

`Merge hook: CPO-QA-Delivery-Contract`

`Merge hook: CTO-Evidence-Policy-Contract`

`Merge hook: CTO-Signing-Release-Contract`

| 门禁 | 决策 owner | 通过条件 |
| --- | --- | --- |
| 机会进入决策 | CEO / CEOChiefOfStaff | 市场雷达线提供足够机会信息，或 CEO 直接提出战略需求 |
| 正式进入主动交付线 | CEO / CEOChiefOfStaff | 明确任务、目标、优先级、约束、owner，以及已由总助预梳理的 intake briefing（包含商业模式 / 阶段适配判断）；默认总助先签、CEO 终签 |
| 模块命中与初始化就绪 | CTO / CPO | 已形成 `ModuleTargetingReport`；涉及既有正式模块时 `ModuleReadinessInit` 已完成；涉及新正式模块时 `NewModuleBaselineRelease=approved` 且 `TriDev init` 已完成 |
| PRD 就绪 | CPO | Discovery 真源草稿、市场证据、运营约束、预算护栏和产品范围可对齐 |
| 技术实施就绪 | CTO | 技术路线、工程门禁、开发任务和依赖边界清楚 |
| TriDev 接入 | CTO / CPO | PRD、验收标准、技术任务和输入证据齐备；若涉及新正式模块，还需 `NewModuleBaselineRelease=approved` 且 `TriDev init` 已完成；若涉及既有正式模块，还需 `ModuleTargetingReport` 与 `ModuleReadinessInit` 已完成 |
| 产品验收 | CPO | 交付产物满足 PRD 与验收标准 |
| 运营接管 | COO | rollout、观察指标、恢复动作和复盘机制明确 |
| 财务决算 | CFO | 实际成本、预算偏差、收益假设和停止条件可复核 |
| 总助收口 | CEOChiefOfStaff | 证据、状态、阻塞、复盘和下一步动作可回填 |

补充说明：对通过 `task-intake` 进入的 CEO freeform 任务，上表中的“正式进入主动交付线”默认还包含 `clarification sheet = ready-for-dispatch`。如果竞品 / 对标对象、目标用户场景、工期、预算、成功信号、最小范围或不做项仍缺失，总助必须先补问一轮，case 不得直接放入 Discovery。

补充说明 2：当 `CEOChiefOfStaff`、`CMO`、`CPO`、`CTO`、`COO`、`CFO` 或未来新增的 `roleAssignmentMatrix.canFreezeCase=true` 岗位在自己负责窗口内做出冻结判断时，case 会进入 `paused-frozen` 并停止后续自动推进；当冻结条件解除后，由原冻结岗位或 `CEOChiefOfStaff` 执行 `unfreeze` 恢复。只有拒签驳回才会把 case 打成 `blocked`。

## 7. 当前阶段边界

- 当前 IPD 流程是 docs-first 的公司级流程设计，优先服务当前 Copilot-host live 阶段。
- 当前 CMO / CPO / COO / CFO / CTO 已进入 Copilot-host live 阶段，但不代表完整授权矩阵、自动数据管道、自动运营看板或自动财务系统已完成。
- 当前 TriDev 已具备 Copilot-host 本地开发执行 engine 可靠性切片，但不代表 ten-stage phase engine 已在 source-side 全量拆开、也不代表完整岗位 adapter、自动任务调度、生产级交付平台或 TriMC 正式宿主已经完成。
- 当前已新增 source-side 一比一 ten-phase runtime slice：CEO / 总助可先创建一条 IPD case；其中总助需先把机会信号、对当前商业模式的适配、对当前阶段的适配、公司现状、owner 建议、资源 envelope、前置条件、所需支持和预期成果整理成 intake briefing，再按“总助先签、CEO 终签”的顺序完成书面签核。签核通过后，runtime 会按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 的顺序生成阶段 work item，并把 `businessOwner / actingOwner / moduleExecutor / gateOwner`、participant roles、input requirements、phase package draft 与总助 / CEO 顺序签核挂到各 phase；autopilot 可自动执行该链路并对接 TriDev 产物。所有阶段都不允许仅靠 docs / workbench 产物假完成，只是各阶段对“真实 evidence”的定义不同：`Discovery / Intelligence / Designing` 需要满足各自真实研究 / 设计产物 contract，`CODING` 到 `DELIVERY` 还额外要求至少一类真实 source / test / deploy / runtime evidence。当前仍不等于 PRD 分叉并行、多分支 delivery 聚合或完整岗位 adapter 已完成。
- 涉及正式宿主边界、长期模块边界或商业模式裁决时，应升级 BusinessStrategy。

## 8. 市场雷达候选采集工具

`CloakHQ/CloakBrowser` 可作为 CMO 市场雷达线的候选浏览器自动化采集工具，用于公开网页、竞品页面、公开评论区、公开榜单、行业新闻和热点页面的市场证据采集验证。

当前只登记为候选工具，不直接写成已生产接入能力，也不直接进入 reference / vendor 吸收链。若后续决定吸收其代码或二进制能力，必须按项目级开源吸收链执行：`TriMetaverse/reference -> 目标模块/vendor -> 真实实现`。

候选事实：

- 上游仓库：`https://github.com/CloakHQ/CloakBrowser`
- 当前定位：Stealth Chromium / Playwright 替代工具，服务 browser automation 与 web scraping 场景。
- 源码许可：仓库 wrapper 源码标注为 MIT License。
- 二进制许可：CloakBrowser Chromium binary 使用单独 Binary License；允许组织内部运行，但限制再分发、转售、重新打包和面向第三方的 SaaS / OEM 嵌入。
- 当前风险：该工具强调反 bot detection、anti-detect、captcha / Cloudflare 场景，必须按合法公开数据采集、站点条款、robots / rate limit、隐私和授权边界使用。

准入门禁：

1. CMO 只可把它用于公开市场信息、竞品公开页面、新闻、公开评论和公开趋势材料的采集验证。
2. 禁止用于未授权登录、绕过认证、账户批量注册、凭证尝试、金融 / 医疗 / 政府等敏感系统访问或任何未授权数据采集。
3. CTO 需先评估安装、运行隔离、二进制来源校验、版本固定、日志、速率限制和失败回滚。
4. CFO 需评估代理、服务器、存储、调用和维护成本。
5. CAO / CompanyGovernanceRegistry 需确认内部使用和许可证边界，不得把二进制打包进对外产品或服务。
6. 只有在 CMO、CTO、CFO 和 CAO 共同确认后，才能进入最小试点。

## 9. Sources

- `TriCompany/docs/product/PROJECT.md`
- `TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md`
- `TriCompany/docs/registry/product-state.md`
- `TriMetaverse/docs/三元宇宙架构与模块说明.md`
- `TriDev/docs/registry/product-state.md`
- `https://github.com/CloakHQ/CloakBrowser`
