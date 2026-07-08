# TriCompany 总助研发编排

版本：V0.6
日期：2026-07-08
状态：新增 §4.8 IPD 系统构建与维护编排 + §4.9 总助编排全景；修复 §4.6 标题丢失

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/workflow/chief-of-staff-rd-orchestration.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/workflow/chief-of-staff-rd-orchestration.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-03

## 1. 文档定位

本文用于定义 TriCompany 当前阶段的总助研发编排方式。它描述的是“在模块源仓里，总助如何协同文档、registry、宿主资产发布与后续岗位”，不是正式宿主 runtime 说明。

本文默认以 `TriCompany/` 为模块真源，以 `TriCompany-copilot-host-assets/` 为当前 Copilot 宿主支撑包，以 `TriMetaverse/.github/` 为当前 live 宿主入口；因此它讨论的是源仓侧编排，不等于 live 入口本身，也不等于 TriMC 正式宿主切换。

## 2. 当前编排目标

1. 让总助成为 TriCompany 当前阶段的研发协调中枢。
2. 让产品、技术和执行层文档保持同步。
3. 让当前阶段 Copilot 宿主相关源码资产统一在 TriCompany/.github 收口，并通过 manifest / 发布动作进入当前 live 宿主入口。
4. 把 Hermes 融合结论沉淀到可直接调用的总助套件里。
5. 协调当前已上岗的 CPO / CTO 接手产品 / 技术真源，并保留未来宿主迁移接口。
6. 以正式签发形式让 CEO 与总助的阶段性对齐结论可以稳定升级到项目真源，而不是停留在会话里。
7. 将各模块 CodeGraph 成果与模块 CodeRegistry 结合使用，汇总收拢到中央 registry，降低总助每次会话的 token 消耗，快速完成模块级代码逻辑和业务逻辑的清洗构建。

## 3. 当前参与角色

- TriCompanyCEOChiefOfStaff：当前总调度与收口中枢。
- TriCompanyProductRegistry：产品真源与产品状态；经营 owner 为 ChiefProductOfficer（CPO，小乔）。
- TriCompanyCodeRegistry：技术真源、结构状态、CodeGraph 摘要与执行层纪律；经营 owner 为 ChiefTechnologyOfficer（CTO，小狄）。
- RAndDTrainer：项目培训内容、模块导读、代码导读和新人学习路径。
- TriCompany/.github：模块侧 `.github` 研发与发布真源。
- TriCompany-copilot-host-assets：当前 Copilot 宿主支撑包与发布后验证支撑层。
- TriMetaverse/.github：当前 live 宿主入口。
- CEO / 当前操作者：当前最高输入来源。
- ChiefProductOfficer：当前 Copilot-host live 阶段已上岗，接手产品范围、MVP、需求优先级、Product Registry 与产品真源持续优化。
- ChiefTechnologyOfficer：当前 Copilot-host live 阶段已上岗，接手技术方案、交付架构、测试 / 发布 readiness、Code Registry 与技术真源持续优化。
- ChiefHumanResourcesOfficer：当前 Copilot-host live 阶段已上岗，接手岗位启用、staffing governance、职责交接流程与 completion tracking。
- ChiefAdministrativeOfficer：当前 Copilot-host live 阶段已上岗，接手行政管理、秘书处机制、会议制度、CompanyGovernanceRegistry 和治理文档归属。

> **TriMetaverse 中央 Registry 说明**：`TriMetaverse/.github/agents/` 下的 `TriMetaverseBusinessStrategyRegistry`、`TriMetaverseProductRegistry`、`TriMetaverseCodeRegistry`、`CompanyGovernanceRegistry` 是 TriMetaverse 项目级的独立中央真源，负责跨模块商业策略裁决、产品/代码状态登记与公司治理；它们不在 TriCompany 源侧管辖范围内，但总助在跨仓协调时需将中央边界裁决纳入分诊判断。冲突时以中央 `BusinessStrategy` 边界裁决为准。

## 4. 当前编排流

### 4.1 事项进入

- 任何关于赛博公司研发、总助设计、Hermes 融合、.github 宿主资产、岗位准备或会议节奏的事项，先进入总助判断。

### 4.2 总助分诊

总助收到事项后，先判断属于哪一类：

- 集成产品开发流程（IPD 流程）：由 TriCompany 承载的公司级端到端经营 / 研发流程，当前采用 `TriCompany IPD 双线闭环`，包含 `IPD 市场雷达线` 与 `IPD 主动交付线`；source-side runtime 已开始按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 提供一比一 ten-phase stage line，并在各 phase 显式挂接 `businessOwner / actingOwner / moduleExecutor / gateOwner`。当前 `TriDev` 是 Discovery 到 Delivery 的统一执行引擎，CPO / CTO 负责对应业务 owner 与 gate owner，`QA` 承担 `release readiness`，未来测试 / 部署执行会转成 `tester-xxx` / `deployer-xxx` 员工 adapter；在新员工未入职前由 CTO 代行。`Discovery` 需先完成 `ModuleTargeting`：既有正式模块走 `ModuleReadinessInit`，新正式模块走 `NewModuleBaselineRelease`。流程细则见 `integrated-product-development-flow.md`。
- 产品范围、角色定位、路线优先级、Product Registry 事实维护：先路由 ChiefProductOfficer（小乔），并回链产品真源与 Product Registry。
- 市场调研、竞品情报、热点抓取、用户需求研究、内容选题、量化事件情报与 PRD 前置证据包：先路由 ChiefMarketingOfficer，并要求其把可复核报告交给 CPO。
- 经营节奏、上线窗口、跨部门执行节律、rollout 计划、试点路径和复盘闭环：先路由 ChiefOperatingOfficer，并回链 operating records、workflow 或 execution 证据。
- 预算规划、成本护栏、盈利检查、价格假设、收入模型、单位经济模型和财务风险：先路由 ChiefFinancialOfficer，并要求区分真实数字、公开报价、人工估算和待确认假设。
- PRD 归属路由、模块设计与 docs 落位判断：由 ChiefProductOfficer 主责；CEOChiefOfStaff 只负责公司级任务分派、排程、催办、升级与收口。
- 技术设计、结构边界、CodeGraph、Hermes 融合与 .github 宿主资产：先路由 ChiefTechnologyOfficer（小狄），并回链技术真源与 Code Registry；架构表中的模块一旦进入正式模块面，默认由 CTO 补齐独立 git 仓、`README.md`、`docs/` 六件套、`.gitignore` 与本地 CodeGraph 初始化，并由对应 Code Registry 维护摘要与刷新节律。对存在治理中 `vendor/` 冻结基线的模块，主 CodeGraph 默认排除 `vendor/`，只在开源吸收 / 差异拆解专项任务下临时纳入 vendor 视图。若为新增正式模块，`Discovery` 阶段必须先形成 `NewModuleBaselineRelease`（含 `vendor-extraction-profile`），经签核后由 `TriDev init` 执行模块骨架初始化；若为既有正式模块，需先形成 `ModuleTargetingReport` 并完成 `ModuleReadinessInit` 后再进入后续开发阶段。
- 会议协调、纪要收口、动作项推进：走会议 prompt 与秘书处草案。
- 项目培训、模块讲解、代码导读、小白 onboarding：同步给 RAndDTrainer，并要求其维护 `docs/training/**` 培训材料、回链真源；CEOChiefOfStaff 只负责同步事实、催办和收口，不长期代写培训文档。
- 跨域问题：由总助组织产品与技术两侧共同收口。

在更多负责人正式上岗后，分诊口径继续扩成：

- COO：当前 Copilot-host live 阶段已上岗，负责经营节奏、rollout、跨部门执行窗口、恢复与复盘闭环。
- CFO：当前 Copilot-host live 阶段已上岗，负责预算、成本护栏、价格例外、结算映射与财务风险。
- CMO：当前 Copilot-host live 阶段已上岗，负责品牌叙事、渠道规划、内容分发、需求捕获、竞品调研、热点抓取和 PRD 前置市场证据。
- CSO：线索管道、成交策略、商机推进与收入执行。
- CHO：岗位启用、人力资源、staffing governance、角色评分卡、跨岗位职责交接流程设计与完成度监督。
- CAO：行政管理、秘书处机制、会议制度、组织制度、CompanyGovernanceRegistry、治理文档归属和公司治理资料维护。
- CCO：当前未上岗，管理 CSM、客服、客户体验与客户成功线。

总助对这些事项的职责仍然是：先分诊、再对齐 owner、必要时升级给 CEO，不替代对应负责人长期代管。

固定 owner 分工：市场雷达线与 PRD 前置市场证据由 CMO 管理，经营节奏与 rollout / 运营接管由 COO 管理，预算护栏、财务风险与决算由 CFO 管理，`ProductRegistry`、PRD、项目计划和产品验收由 CPO 小乔管理，`CodeRegistry`、技术路线、开发实施、所有正式模块的 git / `README.md` / `docs/` 六件套 / CodeGraph 基线、`ModuleTargetingReport` / `ModuleReadinessInit`、`NewModuleBaselineRelease` 执行、`vendor-extraction-profile` 技术口径与 `Git Health` 由 CTO 小狄管理，`docs/training/**` 培训材料由 RAndDTrainer 管理，中央 `CompanyGovernanceRegistry` 由 CAO 管理；Registry 负责事实登记、dirty worktree 基线和升级提示，不直接代替 owner 做本地提交。`CEOChiefOfStaff` 只负责路由、协调、催办、升级和中央收口，不长期代管具体 registry owner。TriDev 的 local engine 当前已开始与 TriCompany IPD runtime 的 ten-phase case line 一比一挂接，并统一承接 Discovery 到 Delivery 的执行层；`QA` 形成 candidate delivery manifest / report 与 `release readiness`，`Delivery` 形成 final manifest / report；`TriTest` / `TriDeployment` 不再作为长期独立执行 owner，后续会收敛为 `tester-xxx` / `deployer-xxx` 员工 adapter，在正式入职前由 CTO 代行。PRD 分叉并行、多分支 delivery 聚合和完整岗位 adapter 仍待继续补齐。

### 4.3 会议入口

- 开始正式讨论时，使用“开始会议”进入正式会议口径。
- 收口结论与动作项时，使用“结束会议”进入纪要与回填口径。

### 4.4 当前阶段宿主资产层

当前阶段宿主相关资产按三层组织：

- `TriCompany/.github/`：模块侧宿主源码与发布前收口资产。
- `TriCompany-copilot-host-assets/`：当前 Copilot 宿主支撑包、验证入口、baseline 与回滚材料。
- `TriMetaverse/.github/`：当前实际生效的 live 宿主入口。

模块侧至少要维护：

- 当前总助 contract 版本。
- 当前 soul / memory / colleagues / social 分层结论。
- 当前会议编排规则。
- 当前 registry 事实与待确认缺口。
- 当前 Hermes 融合与迁移清单。
- 当前 RAndDTrainer 培训目录、模块导读和新人学习路径。

后续新增固定员工、现有员工职责变动、owner 迁移或源侧五件套增量更新时，应先在 TriCompany 源侧完成岗位 / 员工定义、agent 资产、四层记忆资产、岗位职责、协作关系、流程 owner 与 role knowledge workspace 机制，再发布到当前宿主支撑包生成实际消费的 inbox、wiki、audit、workbench、schedule JSON 等对象载荷，并同步核对 binding profile、host object manifest、live discovery 与治理回填。CPO / CTO 本轮采用已有 `TriMetaverse/.github` live entry，不新建第二个 live agent 文件，而是补齐 TriCompany 源侧五件套与 role / employee support object payload。换宿主时迁移的是完整赛博公司源侧定义和流程，而不是在新宿主重新招聘员工或重建流程。

`ChiefHumanResourcesOfficer`（CHO）与 `ChiefAdministrativeOfficer`（CAO）已按源侧链路完成当前 Copilot-host live 启用。CHO 主责制定岗位 / 职责交接流程、handoff checklist 与 completion tracking，并监督交接闭环；CAO 主责行政管理、秘书处机制、会议制度、CompanyGovernanceRegistry 和公司治理资料归属。CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责，不再长期代管这些 owner。

本轮已为 `ChiefHumanResourcesOfficer` 和 `ChiefAdministrativeOfficer` 补齐 TriCompany 源侧岗位定义、五件套、binding profile、host object generation declaration 与 live discovery 入口；该状态只代表当前 Copilot-host live 启用，不等于 TriMC 正式宿主切换或完整授权矩阵生产化。

对应的最小交接治理真源当前落在 `TriCompany/docs/workflow/chief-human-resources-officer-handoff-governance.md`；后续若出现岗位启用、职责移交或长期 owner 切换，应按该文档的 checklist、状态机和验收口径执行。

员工生命周期变更的发布真源落在 `TriCompany/docs/workflow/host-object-publish-flow.md`。当前调试阶段岗位职责和公司流程允许快速迭代；成熟后，同类职责变动、岗位变动和流程变动应由 CHO / CAO / CPO / CTO / CEO 或 BusinessStrategy 按 owner 边界签字确认后再进入正式 live。

RAndDTrainer 当前已作为技术研发培训岗位进入 Copilot-host live 阶段；当前先由 CEOChiefOfStaff 同步项目新增设计、开发实现、模块边界和治理规则。已上岗 CPO / CTO 可分别同步产品、技术和工程流程培训输入。RAndDTrainer 的 role / employee workspace 对象生成、support payload 和 live 入口已具备最小闭环。

### 4.5 跨仓同步条件

当 TriCompany 内形成稳定跨仓结论后，总助才需要准备对外发布与同步，至少包括：

- 哪些结论已稳定。
- 哪些仍待验证。
- 哪些属于当前阶段本地正式接管资产。
- 哪些需要先发布到 `TriCompany-copilot-host-assets/` 再进入 live 宿主。
- 哪些需要升级为跨仓长期规则或中央层摘要。

### 4.6 耐久记忆升级规则

- 如果某项会议结论、边界判断或阶段性工作法需要进入项目耐久真源或岗位耐久记忆，先由总助提出写入建议。
- 建议里至少说明：写入内容、目标文件、写入原因、预计影响范围。
- 由 CEO 明确确认后，再执行仓库回填。
- 未确认的内容可以保留在会话记录、草稿或运行时层，但不自动升级成长期真源。

### 4.7 IPD 双线人工编排操作（当前阶段：总助手动）

> **定位**：本节记录 CEOChiefOfStaff 在 IPD `process-improvement` 与 `project-delivery` 两条 case 线之间的手动协调操作。当前所有跨 case 联动均由总助在对话中完成，IPD 引擎不提供程序化跨 case 编排。本节同时标注未来 TriMC 或自建编排模块的自动化接手点。

#### 4.7.1 操作清单

| 操作 | 触发条件 | 当前执行方式 | 涉及方 | 未来自动化接手点 |
|------|----------|-------------|--------|-----------------|
| **through-pass 审批协调** | process-improvement case 产出流程优化项 | 总助组织 CPO/CTO 填写审批结论，汇总到 backfill 文档 | CPO、CTO | TriMC 可在 workflow sprint review 通过后自动生成审批包并推送 CPO/CTO |
| **through-pass merge 执行** | CPO/CTO 均签 mergeReady=yes | 总助逐项写入 A 层（流程文档）+ B 层（engine/CLI/validation） | 总助 | TriMC 可基于审批结论自动执行文件级 merge，冲突时升级人工 |
| **live replay 验证启动** | merge 完成后 | 总助手动推进 project-delivery case 的 stage 流转，观察验证结果 | CPO、CTO | TriMC 可在 merge 完成后自动触发 project-delivery case 的下一 stage |
| **FREEZE 项回流** | 审批中出现 FREEZE 或 live replay 发现缺陷 | 总助把 FREEZE 项写入下轮 workflow sprint backlog | 总助 | TriMC 可将 FREEZE 项自动追加到对应 WORKFLOW case 的 backlog |
| **缺陷回灌** | project-delivery case 验证失败 | 总助判断回退目标阶段，在 WORKFLOW case 新建 backlog item | CPO、CTO | TriMC 可基于失败 stage 自动生成回灌 backlog item |
| **跨 case 状态同步** | 任一条线有受阻/完成 | 总助在对话中口头同步，必要时更新 operating record | 总助 | TriMC 心跳扫描可自动检测并推送跨 case 卡点 |
| **回写顺序执行** | 流程优化验证通过 | 总助按 B→A→C→D 顺序逐层回写（B=公司执行真源 engine/CLI/validation → A=书面主真源流程文档 → C=联审输入面审批包 → D=操作与实例面执行记录） | CPO、CTO | TriMC 可按回写顺序自动执行并验证每层写入 |

#### 4.7.2 已完成的真实编排案例

**案例 1：首次 through-pass 审批基线合并（2026-07-03，backfill-001）**

```
WORKFLOW-001 产出优化项
  → 总助组织 CPO 审批（7 APPROVE + 3 FREEZE）
  → 总助组织 CTO 审批（8 APPROVE + 2 FREEZE）
  → 总助执行 through-pass merge：
      ├── integrated-product-development-flow.md（A 层，15 项）
      ├── ipd_case_engine.py（B 层，6 项双写）
      ├── chief_of_staff_ipd_case_validation.py（B 层，6 项双写）
      └── 5 项 FREEZE 回流到长期固化清单
  → 主流程升级至 V0.8
```

**案例 2：intake 回退路径补全（2026-07-08）⚠️ 应急修复，未走完整双线验证**

```
CEO 发现 intake 签核后无法回退
  → 总助分析 engine 状态机，发现 rollback --stage-key intake 已存在但不被发现
  → 总助直接在 engine 新增 reopen_intake() + reopen-intake CLI 命令（跳过 process-improvement case 的标准 through-pass 流程）
  → 更新流程图与文档
  → 提交 TriCompany（engine）+ TriMetaverse（docs）

⚠️ 诚实标注：此案例未走 process-improvement → through-pass 审批 → project-delivery 验证的完整双线闭环。
  属 CEO 直接指令下的应急修复，事后应在下一轮 WORKFLOW case 中补回标准验证。
```

#### 4.7.3 自动化接手决策框架

当 TriMC 编排能力上线或考虑自建编排模块时，按以下维度判断每个操作的归属：

| 维度 | 适合 TriMC 自动化 | 适合保留人工 |
|------|------------------|-------------|
| **触发条件** | 明确、可程序化判断（如"CPO mergeReady=yes"） | 需要跨域判断或 CEO 意图解读 |
| **执行动作** | 文件级写入、状态变更、通知推送 | 需要设计决策、冲突调解、创造性工作 |
| **回退路径** | 可逆、有明确回退条件 | 后果不可逆或需要人工承担风险 |
| **频率** | 高频重复操作 | 低频、每次上下文不同 |

**当前建议**：
- 心跳扫描与卡点推送 → 适合 TriMC 优先接手（已在 TriMC/src/heartbeat/ 落地）
- through-pass 审批包生成 → 适合 TriMC 下一批接手
- merge 执行与回写顺序 → 建议先做半自动（TriMC 生成 merge diff，人工确认后执行）
- 缺陷回灌判断 → 当前阶段保留人工，需 CEO/CPO/CTO 判断

#### 4.7.4 与 IPD 引擎的职责边界

```
引擎（ipd_case_engine.py）：
  ✅ 单 case 内阶段状态机、签核链、事件日志
  ✅ intake/stage 级别的 rollback 与 reopen
  ❌ 跨 case 联动（不读另一个 case 的数据）
  ❌ 跨 case 通知（不触发另一个 case 的状态变更）

总助（当前阶段）：
  ✅ 跨 case 协调（WORKFLOW ↔ PLATFORM）
  ✅ through-pass merge 执行
  ✅ FREEZE 回流与 backlog 灌入
  ✅ 回写顺序编排

TriMC / 未来编排模块（规划中）：
  🔲 心跳扫描与卡点检测（已落地 heartbeat）
  🔲 跨 case 状态监控与推送
  🔲 审批包自动生成
  🔲 merge diff 半自动生成
```

### 4.8 IPD 系统构建与维护编排（当前阶段：总助手动）

> **定位**：本节记录 CEOChiefOfStaff 对 IPD 系统本身的构建与维护工作——即引擎、CLI、验证脚本、审批体系、培训材料的从零设计、逐版迭代和 bug 修复。IPD 引擎只管单 case 内的状态机，不管理自身的构建与演进；整个 IPD 系统的"制造者"当前就是总助。

#### 4.8.1 IPD 系统资产清单

**Core Runtime（源侧构建，发布到 copilot-host-assets/runtime/ 执行）：**

| 资产 | 职责 | 首次交付 | 迭代次数 |
|------|------|---------|---------|
| `ipd_case_engine.py` | 十阶段状态机、签核链、双线架构（WORKFLOW/PLATFORM）、case 生命周期 | 2026-06 | 持续迭代 |
| `chief_of_staff_ipd_case.py` | CLI 入口：case create、stage advance、sign-off、rollback、reopen | 2026-06 | 持续迭代 |
| `chief_of_staff_ipd_case_validation.py` | 验证脚本：stage 前置条件、签核有效性、case 完整性 | 2026-06 | 持续迭代 |

**Process Artifacts（through-pass 审批与长期固化体系）：**

| 资产 | 职责 |
|------|------|
| `ipd-first-real-approval-through-pass-checklist.md` | through-pass 审批 checklist |
| `ipd-first-real-approval-role-script.md` | CPO/CTO 审批角色脚本 |
| `ipd-first-real-approval-merge-candidate-matrix.md` | merge 候选矩阵 |
| `ipd-first-real-approval-backfill-record-template.md` | backfill 记录模板 |
| `ipd-first-real-approval-backfill-runbook.md` | backfill 操作 runbook |
| `ipd-first-real-approval-backfill-001.md` | 首个真实审批案例记录 |
| `ipd-long-term-contract-solidification-list.md` | 长期契约固化清单 |
| `ipd-product-acceptance-contract-cpo-review.md` | CPO 产品验收契约 |
| `ipd-runtime-evidence-contract-cto-review.md` | CTO runtime 证据契约 |
| `ipd-company-baseline-checklist.md` | 公司基线 checklist |

**Training Materials：**

| 资产 | 职责 |
|------|------|
| `IPD CASE术语.md` | IPD 术语表 |
| `ipd-usage-guide.md` | IPD 使用指南 |
| `ipd-cli-and-code-workflow-beginner-course.md` | CLI 与代码工作流入门 |
| `ipd-dual-track-optimization-and-merge-flow.md` | 双轨优化与合并流程 |

#### 4.8.2 构建与维护操作

| 操作 | 触发条件 | 当前执行方式 | 未来自动化接手点 |
|------|----------|-------------|-----------------|
| **引擎功能新增** | CPO/CTO/CEO 提出新能力需求（如 intake 回退、through-pass merge 支持） | 总助分析需求→设计状态机变更→编码→本地验证→发布到 copilot-host-assets/runtime/ | TriMC 可在需求审批通过后生成 engine patch，人工 review 后合入 |
| **引擎 bug 修复** | 测试或实际使用中发现行为不符合预期 | 总助定位 bug→修复→验证→发布 | TriMC 可基于 failed validation 日志自动生成修复建议 |
| **CLI 命令扩展** | 新 stage/操作需要 CLI 入口 | 总助新增 argparse 子命令→对接 engine 方法→验证 | TriMC 可通过 engine 方法签名自动生成 CLI 骨架 |
| **验证脚本同步** | engine 变更后需同步验证规则 | 总助逐条核对验证逻辑是否与 engine 行为一致 | TriMC 可从 engine 代码自动提取验证规则并提示差异 |
| **审批体系文档创建** | through-pass 流程首次建立 | 总助设计角色脚本、checklist、merge 矩阵、backfill 模板全套 | 适合保留人工——需理解组织决策逻辑 |
| **培训材料编写** | 新功能上线或新人 onboarding 需要 | 总助编写教程→同步给 RAndDTrainer 维护 | 适合保留人工→未来可由 RAndDTrainer 主导，总助只提供输入 |
| **跨仓同步发布** | engine/文档源侧变更后 | 总助手动将 runtime 副本同步到 copilot-host-assets/runtime/ + 更新发布侧摘要 | TriMC 可在源侧 commit 后自动触发 published-copy sync |
| **双线架构设计调整** | 发现 process-improvement 与 project-delivery 的耦合或 gap | 总助设计架构变更→与 CPO/CTO 对齐→编码+文档同步 | 适合保留人工——涉及组织流程设计决策 |

#### 4.8.3 诚实边界

```
IPD 引擎（ipd_case_engine.py）：
  ✅ 管理 case 内的阶段流转、签核、事件日志
  ❌ 不知道自己的代码是谁写的、怎么迭代的
  ❌ 不知道审批体系文档的存在
  ❌ 不知道培训材料的存在

总助（当前阶段）：
  ✅ 设计并编码了 IPD 引擎的全部功能
  ✅ 创建了 through-pass 审批体系的全部文档
  ✅ 编写了 IPD 培训材料
  ✅ 执行了所有 runtime 跨仓同步发布
  ✅ 修复了所有 IPD 引擎 bug（包括 intake 回退补全）

TriMC / 未来编排模块（规划中）：
  🔲 接管 engine 日常维护的机械化部分（sync、patch 生成、验证同步）
  🔲 心跳扫描与卡点检测（已落地）
  🔲 跨仓 published-copy 自动同步
```

### 4.9 总助编排全景

两条编排线的关系：

```
IPD 系统构建与维护编排（§4.8）
  总助建造轨道：引擎、CLI、审批体系、培训材料
  ─────────────────────────────────────────────
          ↓ 建造完成后，轨道上跑的是 ↓
  ─────────────────────────────────────────────
IPD 双线人工编排操作（§4.7）
  总助在轨道上调度列车：through-pass merge、
  FREEZE 回流、缺陷回灌、跨 case 协调
```

当前阶段，总助既造轨道又调度列车。未来 TriMC 上线后：
- §4.8 的机械化部分（sync、patch、验证同步）→ 交 TriMC
- §4.8 的设计决策部分（架构调整、审批体系设计）→ 保留人工或升级为自建编排模块
- §4.7 的跨 case 协调 → 按 4.7.3 决策框架逐项判断

## 5. 当前约束

- TriCompany 当前既做研发，也承载模块侧宿主源码与发布准备资产，但不等于当前 live 宿主，更不宣称 TriMC 正式宿主运行。当前 IPD engine（`ipd_case_engine.py`）等 runtime 模块的实际执行入口位于 `TriMetaverse/TriCompany-copilot-host-assets/runtime/`；TriCompany 源侧维护源码真源，发布副本由总助同步到 copilot-host-assets 后生效。
- 总助可以组织与收口，但不长期代管产品、技术和公司治理 registry owner；CPO / CTO / CAO 已在当前 Copilot-host live 阶段分别接手 ProductRegistry、CodeRegistry 与 CompanyGovernanceRegistry 的管理入口。
- CPO / CTO 当前上岗不等于 TriMC 正式宿主切换，也不等于产品 / 技术授权矩阵已经全部生产化。
- RAndDTrainer 当前已进入 Copilot-host live 阶段；培训内容不替代项目真源，也不代表 TriMC 正式宿主切换。
- 未经 CEO 明确确认，不把会话记忆、运行时缓存或宿主侧临时补丁直接写成模块真源。

## 6. 下一阶段切换条件

当以下条件满足时，可进入下一阶段（从当前 Copilot-host live 阶段进入 TriMC 正式宿主运行阶段）：

1. 总助首版 contract 在 TriCompany 内已稳定。
2. 模块侧 `.github` 宿主资产已收拢，且发布方向清晰。
3. Hermes 融合与迁移清单已明确。
4. 可持续 cognition 验证与会议回填链已稳定。
5. 最小 schedule / cron / automation staging 路线已明确，并至少完成一条闭环验证。

稳定后，由 CPO / CTO 输出首轮产品 / 技术接管判断，并决定哪些结论继续发布到支撑包、哪些进入 live 宿主、哪些只同步回 TriMetaverse 中央层。
