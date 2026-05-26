# TriCompany Product State

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/registry/product-state.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: active-published-copy
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/registry/product-state.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-05-24

## Module Overview

- TriCompany 是赛博公司的研发仓与经营编排孵化仓。
- 当前职责是沉淀赛博公司产品文档、角色设计、registry、training、Hermes 融合方案和当前阶段 Copilot 宿主资产。
- 当前不是中央战略仓，也不是正式宿主。

## Current Product Scope

- 维护 TriCompany 的项目定位、需求、路线和状态
- 维护总助研发编排、会议机制草案和岗位接管入口
- 维护集成产品开发流程（IPD 流程）：当前采用 `TriCompany IPD 双线闭环`，包含 `IPD 市场雷达线` 与 `IPD 主动交付线`；其中 source-side runtime 已开始按 `DISCOVERY -> INTELLIGENCE -> DESIGNING -> CODING -> VERIFY-INTEGRATION -> REDTEAM -> QA -> DEPLOYMENT -> ASSURANCE -> DELIVERY` 提供一比一 ten-phase stage line，并把公司员工参与、资料与核签要求挂到各 phase
- 维护 Product Registry 的产品事实、用户价值、PRD 归属、能力边界、成熟度和产品状态；经营 owner 为 ChiefProductOfficer（CPO，小乔）
- 维护当前阶段放在 .github 下的 Copilot 宿主资产产品边界
- 维护 Hermes 融合与宿主迁移的产品侧口径
- 维护基于 Hermes 记忆系统吸收并扩展出的四层记忆体系，支撑总助、CTO、CPO 等岗位对象的私域记忆、协作关系与组织共享事实
- 维护 `docs/training/` 培训层，让岗位、模块、代码和流程可被渐进式学习
- 维护本地 Copilot-host 下总助正式接管的产品边界与非正式宿主切换说明
- 维护当前 support root 的临时命名、目标正式名与未来宿主分叉口径

## Current Progress

- 已建立 docs/product、docs/engineering、docs/registry、docs/workflow、docs/execution、docs/training 六层文档基线
- 已建立总助首版研发套件
- 已明确 TriCompany 与 TriMetaverse 的当前边界
- 已确认当前路线为“先在 TriCompany 融合 Hermes，再做 .github 下 Copilot 宿主迁移”
- 已完成 TriMetaverse 侧 shadow-test 回迁与 smoke test
- 已完成一轮完整会议生命周期演练，并确认当前 shadow-test 已闭环
- 已完成本地 Copilot-host 下总助正式接管验证与连续会议链路补证
- 已可统一写成“本地 Copilot-host 已完成 shadow-test，现进入正式接管；该结论不等于正式宿主切换。”
- 已完成 support root 从 `TriCompany-shadow-host` 到 `TriCompany-copilot-host-assets` 的迁移；前者仅保留为 phase-1 历史路径名
- 已安排 ChiefProductOfficer 与 ChiefTechnologyOfficer 在当前 Copilot-host live 入口上岗，并补齐 TriCompany 源侧五件套与 role / employee support object payload；该结论不等于 TriMC 正式宿主切换
- 已新增 ChiefHumanResourcesOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已完成当前 Copilot-host live 启用；该结论不等于 TriMC 正式宿主切换
- 已新增 ChiefAdministrativeOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已完成当前 Copilot-host live 启用；该结论不等于 TriMC 正式宿主切换
- RAndDTrainer 已完成当前 Copilot-host live 启用，作为技术研发培训岗位承接项目培训、模块导读、代码导读和新人学习路径
- 已确认 ProductRegistry 由 CPO 小乔管理；CEOChiefOfStaff 只负责产品事项的公司级路由、协调、催办、升级与中央收口，不长期代管产品 registry owner
- 已确认公司级端到端经营 / 研发流程命名为集成产品开发流程（IPD 流程），由 TriCompany 承载；TriDev 只承接 CPO / CTO 明确边界后的产品开发执行段
- 已新增 `docs/workflow/integrated-product-development-flow.md` 作为 IPD 双线闭环流程真源，明确市场雷达线、主动交付线、TriDev 接入门禁和交付后 CPO / COO / CFO 衔接
- 已把 source-side IPD runtime 从压缩节点切片改写为一条一比一的 ten-phase case line，并把 phase owner、participant roles、gate package 和书面核签挂接到各阶段

## Bug And Gap State

- production 级 Hermes recall / consolidate 仍待进一步验证
- 当前本地正式接管所需的 prompt 交互已形成闭环，但更广泛体验与长期稳定性仍可继续优化
- CPO / CTO 已在当前 Copilot-host live 阶段上岗，且 ProductRegistry / CodeRegistry owner 已明确；但首轮产品 / 技术接管输出和授权矩阵仍需继续验证
- CHO 已接管交接流程设计与完成度监督，CAO 已接管秘书处和行政治理资料归属；CEOChiefOfStaff 保留公司级协调、催办、升级与收口职责
- 部分制度仍是研发草案，不是正式公司制度
- 当前 ten-phase runtime 已落地为一比一 stage line，但 PRD 分叉并行、多分支 delivery 聚合、独立 phase package schema 族、跨岗位 adapter、自动运营监控和正式宿主仍未生产化

## Cross-Module Dependencies

- 依赖 TriMetaverse 的 BusinessStrategy 与赛博公司中央发布口径
- 依赖后续对 Hermes 运行契约与跨仓同步边界的继续确认

## Architecture State

- 当前以产品文档、角色 contract、Hermes 融合、四层记忆体系与本地正式接管宿主资产为主，不承担 TriMC 正式运行宿主职责；当前已完成 shadow-test 收口、本地总助正式接管与连续会议链路闭环
- 未来若进入 `TriMC` 新宿主适配，应新增一套按新宿主要求组织的赛博公司宿主资产文档，复用 workflow，不复用当前 Copilot-host 的 support root 命名
- CPO / CTO / CHO / CAO 当前沿用或新增 `TriMetaverse/.github` live entry；RAndDTrainer 当前使用 `TriCompany/.github/agents/rd-trainer.agent.md` 作为 TriCompany 模块 live entry；TriCompany 源侧五件套和 support object payload 用于 source-side handoff 与后续迁移

## Sources

- ../product/PROJECT.md
- ../product/REQUIREMENTS.md
- ../product/ROADMAP.md
- ../product/STATE.md
- ../workflow/chief-of-staff-rd-orchestration.md
- ../workflow/hermes-copilot-host-migration.md
- ../../README.md
