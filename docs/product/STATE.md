# TriCompany 产品状态

版本：V0.1
日期：2026-04-16
状态：初版

## 文档同步元信息

- sourceOfTruth: TriCompany/docs/product/STATE.md
- publishedFrom: 当前文件（source）
- syncMode: source-only
- publishTier: source-only
- supportPublishedCopy: TriCompany-copilot-host-assets/docs/product/STATE.md
- supportSyncRule: source 稳定语义变更后，active published-copy 需在同轮或下一轮追平
- lastSyncedAt: 2026-06-04

## 当前产品阶段

- 当前处于 Phase 1：Hermes 融合与 .github 宿主迁移

## 已完成

- TriCompany 已作为独立仓库加入工作区
- 已建立首版产品、技术、registry、workflow 和执行层文档骨架
- 已建立首版总助 agent 套件与会议 prompt 入口
- 已确认当前路线改为“先在 TriCompany 融合 Hermes，再做 .github 下 Copilot 宿主迁移”
- 已新增 RAndDTrainer 源侧岗位定义、四层认知资产草案和 `docs/training/` 培训目录初版；RAndDTrainer 已具备最小 support object payload 生成链，并已发布为当前 Copilot-host live 入口
- 已把 CEOChiefOfStaff / 总助补入统一 role / employee support payload 体系，当前 live `.github` 只保留 `ceo-chief-of-staff.agent.md` 入口，四层认知契约回到 TriCompany 源侧五件套，已完成 `knowledge/chief-of-staff/**` legacy 兼容路径退役收口
- 已补 role / employee knowledge workspace 最小源侧 runtime 路径抽象与验证入口
- 已安排 ChiefProductOfficer 与 ChiefTechnologyOfficer 在当前 Copilot-host live 入口上岗，并补齐 TriCompany 源侧五件套、source/support host object manifest 与 role / employee support object payload
- 已新增 ChiefHumanResourcesOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已发布为当前 Copilot-host live 入口
- 已新增 ChiefAdministrativeOfficer 源侧岗位定义、五件套、binding profile 与 host object generation declaration，并已发布为当前 Copilot-host live 入口

## 进行中

- 收口总助在 TriCompany 内的研发编排方式
- 把 Hermes 研究结论转译为总助的认知分层设计
- 把当前阶段 Copilot 宿主资产统一收拢到 TriCompany/.github
- 由总助先同步项目新设计、新实现和模块边界给 RAndDTrainer，逐步更新培训内容
- 由 CPO / CTO 分别接手产品 / 技术真源的持续优化；总助继续协调跨域收口和宿主边界
- 由已上岗 RAndDTrainer 承接技术研发培训内容更新；role / employee workspace 对象生成、总助兼容迁移、CPO/CTO/CHO/CAO 上岗绑定与 support 发布规则已具备最小闭环
- 已上线 TriCompany 模块级 orchestrator agent（`TriCompany.agent.md`）：负责源侧→发布侧同步链路总控、发布清单维护与发布纪律执行；CPO/CTO/CAO 三方 APPROVE（2026-07-24）；当前 Phase 1 仅实现 Copilot-host 同步，多宿主适配为架构占位

## 待推进

- 让 CPO / CTO 开始输出首轮产品 / 技术接管判断，并与总助、registry 形成固定分诊闭环
- 评估哪些稳定结论需要跨仓同步回 TriMetaverse
- 把 role / employee workspace 从当前对象生成推进到跨员工 LLM wiki refresh、schedule 模板和 live 运行节律补证

## 当前风险

- TriCompany 虽承载当前阶段试运行宿主资产，但仍不是正式宿主；若边界写乱，后续会返工
- CPO / CTO 虽已在当前 Copilot-host live 阶段上岗，但首轮接管输出、授权矩阵和长期运行节律仍需验证；不得写成 TriMC 正式宿主或生产级组织运行完成
- CHO / CAO / RAndDTrainer 已在当前 Copilot-host live 阶段上岗，但该状态不得写成 TriMC 正式宿主切换或完整授权矩阵生产化
- Hermes 运行契约和 .github 宿主资产当前仍需后续验证
- 培训内容若脱离真源独立演化，会变成第二套解释系统并制造事实漂移

## 待确认

- TriCompany 的正式模块地位
- CPO / CTO / CHO / CAO / RAndDTrainer 上岗后的授权矩阵、首轮接管节奏和跨岗位同步机制
- 总助 Cognition 层的最终运行方式
